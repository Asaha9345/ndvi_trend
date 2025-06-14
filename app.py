import streamlit as st
import geopandas as gpd
import ee
import geemap
import geemap.foliumap as gmap
import json
import datetime
from google.oauth2 import service_account

st.set_page_config(layout="wide")
st.title("🌳 NDVI Trend analysis")
shapefile = gpd.read_file("India_block_wise_shape.shp")
states = ["Select State"]+sorted(list(set(shapefile["State"])))
state = st.selectbox("Select the state",states)
if not state=="Select State":
    dustricts = ["Select District"]+sorted(list(set(shapefile[shapefile["State"]==state]["District"])))
    district = st.selectbox("Select the district",dustricts)
    if not district=="Select District":
        col1, col2 = st.columns([1,1])
        with col1:
            current_year = datetime.datetime.now().year
            start_year = st.number_input("Enter the Start date",min_value=2015,max_value=(current_year-4))
        with col2:
            current_year = datetime.datetime.now().year
            end_year = st.number_input("Enter the end date",min_value=(start_year+4),max_value=(current_year))

        if st.button("Run"):
            if not all([district, start_year, end_year]):
                st.warning("Please fill all the fields")
            else:
                # Load service account info from Streamlit secrets
                service_account_info = st.secrets["GCP_SERVICE_ACCOUNT"]
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                # Initialize Earth Engine with the credentials
                ee.Initialize(credentials)
                gdf = shapefile[shapefile["District"]==district]
                region = gdf.to_json()
                json_dict = json.loads(region)
                aoi = ee.FeatureCollection(json_dict)
                inputs = {"project_id":project_id,
                            "years":[start_year,end_year],
                            "aoi": aoi}
                from trend_analysis import get_trend
                trend_map = get_trend(inputs)
                Map = gmap.Map()
                vis_params = {
                    'min': -0.05,
                    'max': 0.05,
                    'palette': ['red', 'white', 'green']
                }

                aoi_outline = aoi.style(**{
                    'color':'blue',
                    'fillColor':'0000',
                    'width':2
                })
                Map.addLayer(aoi_outline, {}, "Area of Intrest")
                Map.addLayer(trend_map, vis_params, "NDVI Trend Map")
                Map.centerObject(aoi)
                Map.to_streamlit()
