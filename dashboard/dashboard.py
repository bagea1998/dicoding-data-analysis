import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import pathlib
from streamlit_folium import folium_static, st_folium
from io import StringIO
import matplotlib
import numpy as np
from scipy.interpolate import griddata

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

base_url = "https://raw.githubusercontent.com/bagea1998/dicoding-data-analysis/master/dataset/"
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

with open('dashboard/style_.css') as f:
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

st.write(df_AirQuality.head())
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
    height=600,
    width=1400,
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


st.markdown('### Spatio-Temporal Distribution of PM 2.5')
df_animated = (df_AirQuality.groupby(['station','hour'])['PM2.5'].median().reset_index()).merge(gdf_station, left_on='station', right_on='name',how='left')

df_grid = {'hour' : [],
            'grid_value' : [],
            'grid_lat' : [],
            'grid_lon' : [],}
for jam in df_animated['hour'].unique():
    df = df_animated[df_animated['hour']==jam]
    koordinat = df[['lon', 'lat']].values
    value = df['PM2.5'].values

    grid_lon, grid_lat = np.meshgrid(
        np.linspace(df['lon'].min(), df['lon'].max(), 170),
        np.linspace(df['lat'].min(), df['lat'].max(), 170)
    )

    grid = griddata(koordinat, value, (grid_lon, grid_lat), method='cubic')

    df_grid['hour'].append(jam)
    df_grid['grid_value'].append(grid)
    df_grid['grid_lat'].append(grid_lat)
    df_grid['grid_lon'].append(grid_lon)

df_grid = pd.DataFrame(df_grid)
df_flat = []
for i in range(len(df_grid)):
    latitude = df_grid['grid_lat'].values[i]
    longitude = df_grid['grid_lon'].values[i]
    value = df_grid['grid_value'].values[i]

    lat_flat = latitude.flatten()
    lon_flat = longitude.flatten()
    value_flat = value.flatten()

    df = pd.DataFrame({
        'Latitude': lat_flat,
        'Longitude': lon_flat,
        'value': value_flat,
        'hour' : i
    })
    df_flat.append(df)
df_flat = pd.concat(df_flat, ignore_index=True)
mapbox_token = 'your_mapbox_token_here'
px.set_mapbox_access_token(mapbox_token)

fig = px.scatter_mapbox(
    df_flat,  
    lat='Latitude', 
    lon='Longitude', 
    color='value',
    animation_frame="hour",
    color_continuous_scale=px.colors.cyclical.IceFire, 
    size_max=15, 
    zoom=10,
    mapbox_style="open-street-map",
    title=f'Interpolation PM 2.5',
    range_color=(30, 75)
)

fig.add_scattermapbox(
    lat=gdf_station['lat'],
    lon=gdf_station['lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='black',
        opacity=0.7
    ),
    text=gdf_station['name'],
    hoverinfo='text'
)
fig.add_scattermapbox(
    lat=gdf_station['lat'],
    lon=gdf_station['lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='black',
        opacity=0.7
    ),
    text=gdf_station['name'],
    hoverinfo='text',
    showlegend=False
)
fig.update_layout(
    height=1000, 
    width=1400,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        title_text="stasiun"
    )
)
fig.update_layout(
    height=1100, 
    width=1400    
)
st.plotly_chart(fig)