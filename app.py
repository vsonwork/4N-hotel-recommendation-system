import streamlit as st
from streamlit_folium import folium_static
import folium
import numpy as np
import pandas as pd
import geocoder
from streamlit_option_menu import option_menu

st.set_page_config(
	page_title = "Hotel Recommender",
	page_icon = "🏨",
)

if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False

def callback():
    st.session_state.button_clicked = True

selected = option_menu(None, ["Hotel Recommendation Map"],
    icons=['house'],
    menu_icon="cast", default_index=0, orientation="horizontal")

#pickle model for hotel review
hotel_review = pd.read_parquet('data/clean_hotelreview.parquet.gzip')
cosine = np.load('data/reviewcosine.npy')

#pickle model for hotel tags
similarity = np.load('data/tagcosine.npy')
hotel_tags = pd.read_parquet('data/clean_hoteltag.parquet.gzip')

#st.title('Hotel Recommendation')

hotel_select = st.sidebar.selectbox(
    '**Choose a hotel**',
    hotel_review['hotel_name'].unique(),
    index=None,
    placeholder="Select hotel name...",
)

country_select = st.sidebar.selectbox(
    '**Choose a city**',
    hotel_review['city'].unique(),
    index=None,
    placeholder="Select city ...",
)

genre = st.sidebar.radio(
    "**Recommended by**",
    [":rainbow[Tags]", ":rainbow[Reviews]"],
    index=None,
)

# function for getting list of hotels based on hotel reviews
def new_recommendations(name, city, cosine_similarities=cosine):
    recommended_hotels = []

    # get input city index
    city_index = list(hotel_review[hotel_review.city == city].index)

    # gettin the index of the hotel that matches the name
    idx = hotel_review[(hotel_review.hotel_name == name)].index[0]

    # creating a Series with the similarity scores in descending order
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending=False)

    # getting the indexes of the 10 most similar hotels except itself
    top_10_indexes = list(score_series.index)

    # populating the list with the names of the top 10 matching hotels
    for i in range(len(top_10_indexes)):
        if top_10_indexes[i] not in city_index:
            pass
        else:
            recommended_hotels.append(hotel_review[hotel_review.index == top_10_indexes[i]]['hotel_name'].values[0])

    h = hotel_review[['hotel_name', 'lat_x', 'lng_x']].to_dict(orient='records')
    l = {k['hotel_name']: [k['lat_x'], k['lng_x']] for k in h}
    if {hotel: l[hotel] for hotel in recommended_hotels} == {}:
        st.info("There are no hotels of similar hotel")
    else:
        output = {hotel: l[hotel] for hotel in recommended_hotels[:10]}
        newoutput = {i: output for i in range(1, len(output) + 1)}
        return newoutput


# function to pin the hotels on folium
def get_hotel(data, mydict, city, genre):
    loc2 = geocoder.osm(city)

    # map
    main_map = folium.Map(location=[loc2.lat, loc2.lng], zoom_start=13)
    #folium.raster_layers.TileLayer('Open Street Map').add_to(main_map)

    # loop through dict
    for i in range(1, len(mydict) + 1):
        idx = data.loc[data["hotel_name"] == list(mydict[i].keys())[i - 1]].index
        # create an iframe pop-up for the marker
        popup_html = f"<b>Hotel:</b> {data.loc[idx, 'hotel_name'].to_string()}<br/>"
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={tuple(list(mydict[i].values())[i - 1])}"
        popup_html += f'<a href="{directions_url}" target="_blank">Get directions</a><br/><br/>'
        if genre == 'Reviews':
            popup_html += f"<b>Review:</b> {''.join(data.loc[idx, 'review_text_clean'].tolist())}"
        else:
            popup_html += f"<b>Tags:</b> {', '.join(', '.join(tag) for tag in data.loc[idx, 'new_tags'])}"

        popup_iframe = folium.IFrame(width=200, height=110, html=popup_html)

        folium.Marker(location=list(mydict[i].values())[i - 1],
                      tooltip=str(list(mydict[i].keys())[i - 1]),
                      popup=folium.Popup(popup_iframe),
                      icon=folium.CustomIcon(
                                            f"https://raw.githubusercontent.com/vsonwork/4N-hotel-recommendation-system/main/icon/icon{i}.png",
                                            icon_size=(37.185, 50.25)
                                            )).add_to(main_map)

    return main_map


# function to get recommendation for tags,output as dictionary
def new_recommendations_tags(name, city, cosine_similarities):
    recommended_hotels = []

    # get input city index
    city_index = list(hotel_tags[hotel_tags.city == city].index)

    # gettin the index of the hotel that matches the name
    idx = hotel_tags[(hotel_tags.hotel_name == name)].index[0]

    # creating a Series with the similarity scores in descending order
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending=False)

    # getting the indexes of the 10 most similar hotels except itself
    top_10_indexes = list(score_series.index)

    # populating the list with the names of the top 10 matching hotels
    for i in range(len(top_10_indexes)):
        if top_10_indexes[i] not in city_index:
            pass
        else:
            recommended_hotels.append(hotel_tags[hotel_tags.index == top_10_indexes[i]]['hotel_name'].values[0])

    h = hotel_tags[['hotel_name', 'lat_x', 'lng_x']].to_dict(orient='records')
    l = {k['hotel_name']: [k['lat_x'], k['lng_x']] for k in h}
    if {hotel: l[hotel] for hotel in recommended_hotels} == {}:
        st.info("There are no hotels of similar hotel")
    else:
        output = {hotel: l[hotel] for hotel in recommended_hotels[:10]}
        newoutput = {i: output for i in range(1, len(output) + 1)}
        return newoutput


# Add the map to the streamlit app
#directions_button = st.sidebar.button('🔎 Search')
if (st.sidebar.button('🔎 Search', on_click=callback)
        or st.session_state.button_clicked):
    if hotel_select and country_select and genre:
        if genre == ":rainbow[Tags]":
            folium_static(
                get_hotel(data=hotel_tags,
                          mydict=new_recommendations_tags(hotel_select,country_select,cosine_similarities=similarity),
                          city=country_select,
                          genre='Tags'))
        elif genre == ":rainbow[Reviews]":
            folium_static(
                get_hotel(data=hotel_review,
                          mydict=new_recommendations(hotel_select, country_select, cosine_similarities=cosine),
                          city=country_select,
                          genre='Reviews'))
else:
    st.image('image/HOTEL.png', caption='Created by 4N')
	
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
