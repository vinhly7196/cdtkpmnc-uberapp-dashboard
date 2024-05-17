import streamlit as st
import pandas as pd
import requests
import json 
import matplotlib.pyplot as plt
from citys import citys_list
import seaborn as sns
import unicodedata
import plotly.express as px
import numpy as np
import plost

BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)

def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)

# get api trip
res = requests.get('http://209.38.168.38/trip/get')
response = json.loads(res.text)
jsondict = json.dumps(response)
df =  pd.read_json(jsondict, orient='records')

# add new columns 
df['city'] = df.apply(lambda row: row.pickup['address'].split(',')[3], axis=1)
df['district'] = df.apply(lambda row: row.pickup['address'].split(',')[2], axis=1)
df['request_date'] = df['request_time'].dt.date
df['pickup_lat'] = df.apply(lambda row: row.pickup['coordinate'][1], axis=1)
df['pickup_lng'] = df.apply(lambda row: row.pickup['coordinate'][0], axis=1)

# get api vehicle type
vehicles_res = requests.get('http://209.38.168.38/vehicle/vehicle-types')
veh_response = json.loads(vehicles_res.text)
veh_jsondict = json.dumps(veh_response)
veh_df =  pd.read_json(veh_jsondict, orient='records')
vehicles = veh_df["name"].drop_duplicates().tolist()


st.set_page_config(layout='wide', initial_sidebar_state='expanded')

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
st.sidebar.header('Dashboard `version 2`')


# filter source
sources = ['customer', 'call-center']
st.sidebar.subheader('Source')
SOURCES_SELECTED = st.sidebar.multiselect('BOOK BY', sources) 

# filter by year and month
st.sidebar.subheader('Date')
years = df['request_time'].dt.year.drop_duplicates().tolist()
months = df['request_time'].dt.month.drop_duplicates().tolist()

YEAR_SELECTED = st.sidebar.selectbox('Select Year', years)
MONTHS_SELECTED = st.sidebar.multiselect('Select Months', months)

# filter by vehicle type
st.sidebar.subheader('Vehicle Type')
VEHICLE_TYPE_SELECTED = st.sidebar.multiselect('Select Vehicle Types', vehicles) 

# filter by sector
cities = []
for c in citys_list:
    cities.append(c["city"])


st.sidebar.subheader('City')
CITY_SELECTED = st.sidebar.multiselect('Select City', cities) 


st.sidebar.markdown('''
---
DO AN CHUYEN DE THIET KE PHAN MEM NANG CAO.
''')

# filter dataframe
if len(SOURCES_SELECTED) != 0:
    df = df.loc[df["request_from"].isin(SOURCES_SELECTED)]

df = df.loc[df["request_time"].dt.year == YEAR_SELECTED]
if len(MONTHS_SELECTED) != 0:
    df = df.loc[df["request_time"].dt.month.isin(MONTHS_SELECTED)]

if len(VEHICLE_TYPE_SELECTED) != 0:
    df = df.loc[df["vehicle_type"].isin(VEHICLE_TYPE_SELECTED)]

rows_list = []
if len(CITY_SELECTED) != 0:
    for city in CITY_SELECTED:
        for index, row in df.iterrows():
            if city in (row['city']) or xoa_dau(city) in (row['city']):
                rows_list.append(row)
    df = pd.DataFrame(rows_list)               



# Row A
st.markdown('### Metrics')
col1, col2, col3 = st.columns(3)
price_sum = 0
distance_sum = 0
id_count = 0
if not df.empty:
    price_sum = df['price'].sum()
    distance_sum = df['distance'].sum()
    id_count = df['id'].count()
col1.metric("Revenue", f"{price_sum:,.0f} ₫")
col2.metric("Distance", f"{distance_sum:,.0f} km", "-8%")
col3.metric("Trip", id_count, "4%")


if not df.empty:
    c1, c2 = st.columns((5,5))
    with c1:
        st.markdown('### Donut Chart')
        df_payment = df.groupby(['payment_method']).agg({'id': 'count'}).reset_index()
        figp, axp = plt.subplots()
        axp.pie(df_payment['id'],labels=df_payment["payment_method"],
                autopct='%1.1f%%', pctdistance=0.85)
        axp.axis('equal')
        st.pyplot(figp)
    
    with c2:
        st.markdown('### Pie chart')
        df_request = df.groupby(['request_from']).agg({'price': 'sum'}).reset_index()
        fig1, ax1 = plt.subplots()
        ax1.pie(df_request['price'], autopct='%1.1f%%',labels=df_request["request_from"],
                shadow=True, startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

    


    # Row C
    st.markdown('### Line chart')
    # Create a Seaborn pairplot
    fig = plt.figure(figsize=(10, 4))
    # sns.lineplot(data=df, x='request_date', y='price', hue='district')
    sns.barplot(data=df, x='request_date', y='price').set(ylabel='Revenue', xlabel='Request Date')

    
    # Display the plot in Streamlit
    st.pyplot(fig)


    # row D
    st.markdown('### Bar chart')
    fig1 = plt.figure(figsize=(10, 4))
    sns.countplot(x="vehicle_type", data=df, hue='request_type').set(ylabel='Book', xlabel='Vehicle Type')
    st.pyplot(fig1)

    # row E
    midpoint = (np.average(df['pickup_lat']), np.average(df['pickup_lng']))
    print(midpoint)
    fig2 = px.scatter_mapbox(df, 
                        lat="pickup_lat", 
                        lon="pickup_lng", 
                        zoom=12, 
                        height=800,
                        width=800)
    fig2.update_layout(
        mapbox_style='open-street-map', 
        autosize=True,
        mapbox = { 'center': dict(lat=midpoint[0], lon=midpoint[1]) }
        )
    st.plotly_chart(fig2, use_container_width=True)