import streamlit as st
import pandas as pd
import requests
import json 
import matplotlib.pyplot as plt
from citys import citys_list
import seaborn as sns
import plotly.express as px
import numpy as np
import controller
import datetime
from matplotlib.ticker import NullFormatter
import matplotlib.ticker as ticker

GET_ALL_TRIP_API = 'http://209.38.168.38/trip/get?skip=0&limit=0'
GET_VEHICLE_TYPE_API = 'http://209.38.168.38/vehicle/vehicle-types'

# get api trip
df = controller.get_data(GET_ALL_TRIP_API)

# add new columns 

df['city'] = df.apply(lambda row: row.pickup['address'].split(',')[3], axis=1)
df['district'] = df.apply(lambda row: row.pickup['address'].split(',')[2], axis=1)
df['request_date'] = df['request_time'].dt.date
df['request_year'] = df['request_time'].dt.year
df['request_month'] = df['request_time'].dt.month
df['dates'] = df['request_time'].dt.strftime('%Y-%m')
df['vehicle_type'] = df.apply(lambda row: row.vehicle_type['name'], axis=1)
df['pickup_lat'] = df.apply(lambda row: row.pickup['coordinate'][1], axis=1)
df['pickup_lng'] = df.apply(lambda row: row.pickup['coordinate'][0], axis=1)

df['customer_id'] = df.apply(lambda row: row.customer['id'], axis=1)
df['customer_name'] = df.apply(lambda row: row.customer['name'], axis=1)
df['customer_phone'] = df.apply(lambda row: row.customer['phone'], axis=1)
df = df.drop(['customer'], axis=1)

# get api vehicle type
veh_df = controller.get_data(GET_VEHICLE_TYPE_API)
vehicles = veh_df["name"].drop_duplicates().tolist()


st.set_page_config(layout='wide', initial_sidebar_state='expanded')

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
st.sidebar.header('Dashboard')


# filter source
sources = ['customer', 'call-center']
st.sidebar.subheader('Source')
SOURCES_SELECTED = st.sidebar.multiselect('BOOK BY', sources) 

# filter by year and month
st.sidebar.subheader('Date')


today = datetime.datetime.now()
next_year = today.year + 1
begin = datetime.date(today.year, 1, 1)
end = datetime.date(today.year, 12, 31)
min = datetime.date(today.year, 1, 1)
max = datetime.date(next_year + 10, 12, 31)

d = st.sidebar.date_input(
    "Select your Date Range",
    (begin, end),
    min,
    max,
    format="DD.MM.YYYY",
)

# filter by vehicle type
st.sidebar.subheader('Vehicle Type')
VEHICLE_TYPE_SELECTED = st.sidebar.multiselect('Select Vehicle Types', vehicles) 

# filter by sector
cities = []
for c in citys_list:
    cities.append(c["city"])


st.sidebar.subheader('City')
CITY_SELECTED = st.sidebar.multiselect('Select City', cities) 

st.sidebar.subheader('Driver')
DRIVER_SELECTED = st.sidebar.text_input('Driver ID') 

st.sidebar.subheader('Customer')
CUSTOMER_SELECTED = st.sidebar.text_input('Customer ID') 

# filter dataframe
df = df.loc[df["status"] == "Done"]

# add column driver ID
df['driver_id'] = df.apply(lambda row: row.driver['id'], axis=1)
df['driver_name'] = df.apply(lambda row: row.driver['name'], axis=1)
df['driver_phone'] = df.apply(lambda row: row.driver['phone'], axis=1)
df = df.drop(['driver'], axis=1)


if len(SOURCES_SELECTED) != 0:
    df = df.loc[df["request_from"].isin(SOURCES_SELECTED)]


MONTHS_SELECTED = False
if d != None:
    date_start = d[0]
    date_end = date_start
    if len(d) == 2: 
        date_end = d[1]
    df = df.loc[(df["request_date"] >= date_start) & (df["request_date"] <= date_end)]

    if date_start.month == date_end.month and date_start.year == date_end.year:
        MONTHS_SELECTED = True


if len(VEHICLE_TYPE_SELECTED) != 0:
    df = df.loc[df["vehicle_type"].isin(VEHICLE_TYPE_SELECTED)]

rows_list = []
if len(CITY_SELECTED) != 0:
    for city in CITY_SELECTED:
        for index, row in df.iterrows():
            if city in (row['city']) or controller.xoa_dau(city) in (row['city']):
                rows_list.append(row)
    df = pd.DataFrame(rows_list)               

if DRIVER_SELECTED != "":
    df = df.loc[df["driver_id"] == DRIVER_SELECTED]

if CUSTOMER_SELECTED != "":
    df = df.loc[df["customer_id"] == CUSTOMER_SELECTED]


# CREATE DOWNLOAD REPORT
df_months = pd.DataFrame()
df_months = df.groupby(['request_year', 'request_month']).agg({'price': 'sum'})
df_months = df_months.rename(columns= {'price':'Revenue'})
csv = controller.convert_df(df)

st.sidebar.download_button(
    label="Download report line item",
    data=csv,
    file_name="report.csv",
    mime="text/csv",
)

csv_months = controller.convert_df(df_months)

st.sidebar.download_button(
    label="Download report by months",
    data=csv_months,
    file_name="monthly_report.csv",
    mime="text/csv",
)

st.sidebar.markdown('''
---
DO AN CHUYEN DE THIET KE PHAN MEM NANG CAO.
''')


# Row A
st.markdown('### Metrics')
col1, col2, col3 = st.columns(3)
price_sum = 0
distance_sum = 0
id_count = 0
id_done_count = 0
id_done_rate = 0
if not df.empty:
    price_sum =     df['price'].sum()
    distance_sum =  df['distance'].sum()
    id_done_count = df['id'].count()
    id_count = df['id'].count()
    id_done_rate = id_done_count * 100 / id_count
col1.metric("Revenue", f"{price_sum:,.0f} ₫")
col2.metric("Distance", f"{distance_sum:,.0f} km")
col3.metric("Trip Done", id_done_count, f"{id_done_rate:,.0f}%")


if not df.empty:
    df = df.sort_values(by='request_date', ascending=True)

    c1, c2 = st.columns((5,5))
    with c1:
        st.markdown('### Pie Chart')
        df_payment = df.groupby(['payment_method']).agg({'id': 'count'}).reset_index()
        figp, axp = plt.subplots()
        axp.pie(df_payment['id'],labels=df_payment["payment_method"],
                autopct='%1.1f%%', pctdistance=0.85)
        axp.axis('equal')
        st.pyplot(figp)
    
    with c2:
        df_request = df.groupby(['request_from']).agg({'price': 'sum'}).reset_index()
        fig1, ax1 = plt.subplots()
        ax1.pie(df_request['price'], autopct='%1.1f%%',labels=df_request["request_from"],
                shadow=True, startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

    
    # Row C
    st.markdown('### Revenue By Date Chart')
    # Create a Seaborn pairplot
    # fig, ax = plt.figure(figsize=(10, 4))
    fig, ax = plt.subplots(1,1)
    # sns.lineplot(data=df, x='request_date', y='price', hue='district')

    # filter by months 
    if MONTHS_SELECTED:
        fig, ax = plt.subplots(figsize=(8, 5)) 
        g = sns.barplot(data=df, x='request_date', y='price', estimator=sum, ci=None).set(ylabel='Revenue', xlabel='Request Date')
        xticks = ax.get_xticks()
        xticklabels = [x.get_text() for x in ax.get_xticklabels()]
        _ = ax.set_xticks(xticks, xticklabels, rotation=45)
        ax.yaxis.set_major_formatter(controller.formatter)
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_ylabel("triệu đồng")


    else:
        fig, ax = plt.subplots(figsize=(8, 5))    
        g = sns.barplot(data=df, x='dates', y='price', estimator=sum, ci=None).set(ylabel='Revenue', xlabel='Request Month')

        ax.yaxis.set_major_formatter(controller.formatter)
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_ylabel("triệu đồng")

    # Display the plot in Streamlit
    st.pyplot(fig)


    # row D
    st.markdown('### Revenue By Car Type Chart ')
    fig1, ax1 = plt.subplots(figsize=(8, 5)) 
    g1 = sns.barplot(data=df, x='vehicle_type', y='price', estimator=sum, ci=None).set(ylabel='Revenue', xlabel='Vehicle Type')
    ax1.yaxis.set_major_formatter(controller.formatter)
    ax1.yaxis.set_minor_formatter(NullFormatter())
    ax1.set_ylabel("triệu đồng")
    st.pyplot(fig1)

    # row E
    st.markdown('### Pickup Positions')
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