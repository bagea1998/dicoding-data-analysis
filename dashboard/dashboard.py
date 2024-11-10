import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
from scipy.interpolate import griddata
import pathlib
from streamlit_folium import folium_static, st_folium
from io import StringIO

# import data

coordinates = [
    {"name": "Aotizhongxin", "lat": 39.9828, "lon": 116.3924},
    {"name": "Changping", "lat": 40.2264, "lon": 116.2312},
    {"name": "Dingling", "lat": 40.2905, "lon": 116.2203},
    {"name": "Dongsi", "lat": 39.9290, "lon": 116.4175},
    {"name": "Guanyuan", "lat": 39.9296, "lon": 116.3576},
    {"name": "Gucheng", "lat": 39.9078, "lon": 116.1766},
    {"name": "Huairou", "lat": 40.3174, "lon": 116.6318},
    {"name": "Nongzhanguan", "lat": 39.9331, "lon": 116.4612},
    {"name": "Shunyi", "lat": 40.1289, "lon": 116.6540},
    {"name": "Tiantan", "lat": 39.8826, "lon": 116.4061},
    {"name": "Wanliu", "lat": 39.9673, "lon": 116.3064},
    {"name": "Wanshouxigong", "lat": 39.8882, "lon": 116.3539}
]

df_StationCoordinates = pd.DataFrame(coordinates)
df_StationCoordinates['geometry'] = df_StationCoordinates.apply(lambda row: Point(row.lon, row.lat), axis=1)

gdf_station = gpd.GeoDataFrame(df_StationCoordinates, geometry='geometry', crs='EPSG:4326')


base_url = "https://raw.githubusercontent.com/bagea1998/dicoding-data-analysis/master/PRSA_Data_20130301-20170228/"
station_names = [
    "Aotizhongxin", "Changping", "Dingling", "Dongsi", "Guanyuan", 
    "Gucheng", "Huairou", "Nongzhanguan", "Shunyi", "Tiantan", 
    "Wanliu", "Wanshouxigong"
]

list_df = []
for station in station_names:
    file_url = f"{base_url}PRSA_Data_{station}_20130301-20170228.csv"
    try:
        df = pd.read_csv(file_url, on_bad_lines='skip')
        list_df.append(df)
    except pd.errors.ParserError as e:
        print(f"Error reading {file_url}: {e}")

df_AirQuality = pd.concat(list_df, ignore_index=True)

# data_dir = pathlib.Path(r'G:/Data_Analis/Python/code/tugas_akhir_analisis_data_dicoding/PRSA_Data_20130301-20170228')
# csv_files = list(data_dir.rglob('*.csv'))
# list_df = []
# for  file in csv_files:
#     df = pd.read_csv(file)
#     list_df.append(df)
# df_AirQuality = pd.concat(list_df, ignore_index=True)


# apps
st.set_page_config(layout='wide', initial_sidebar_state='expanded')

with open('style_.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# with open(r'G:/Data_Analis/Python/code/tugas_akhir_analisis_data_dicoding/style_.css') as f:
#     st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.sidebar.subheader('Air Quality Dashboard')

st.markdown('### Distribution of Station')
map = gdf_station.explore(
    'name',
    marker_kwds={
        'radius': 10,      
        'fill': True,          
        'opacity': 1
    }
)

st_folium(map, width=1400, height=600)

df_2017 = df_AirQuality[df_AirQuality['year'] == 2017]
parameters = df_AirQuality.columns[5:11]

agg_df = df_2017.groupby('station')[parameters].median().reset_index()

st.markdown('### Top 3 Stations with Highest Median Air Quality Parameters in 2017')
fig = go.Figure(make_subplots(rows=3, cols=2, 
                              subplot_titles=[f"Median {param}" for param in parameters],
                              vertical_spacing=0.15, horizontal_spacing=0.1))

for i, parameter in enumerate(parameters):

    row, col = divmod(i, 2)
    row += 1
    col += 1

    data = agg_df[['station', parameter]].nlargest(3, parameter)

    colors = ['steelblue'] * 3
    max_index = data[parameter].idxmax()
    colors[data[parameter].index.get_loc(max_index)] = '#FF3333'

    fig.add_trace(go.Bar(
        y=data['station'],
        x=data[parameter],
        orientation='h',
        marker=dict(color=colors),
        name=f"Median {parameter}",
        text=[f"{value:.2f}" for value in data[parameter]],
        textposition='inside',
    ), row=row, col=col)

fig.update_layout(
    title_text="",
    title_x=0.5,
    showlegend=False,
    height=1000,
    width=1200,
    template="plotly_white"
)

st.plotly_chart(fig)

st.markdown('### Trend PM2.5 per Station from 2013 until 2017')

data = df_AirQuality.groupby(['year', 'station'])['PM2.5'].median().reset_index()

fig = px.line(data, x='year', y='PM2.5', color='station', 
              title='Trend PM2.5 per Station dari 2013 hingga 2017',
              labels={'year': 'Year', 'PM2.5': 'PM2.5 Concentration', 'station': 'Station'},
              markers=True)

fig.update_layout(
    legend_title="Station",
    legend=dict(x=1.05, y=1),
    margin=dict(r=40)
)

st.plotly_chart(fig)