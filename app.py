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

# Load the shapefile once
try:
    shapefile = gpd.read_file("India_block_wise_shape.shp")
except Exception as e:
    st.error(f"Error loading shapefile: {e}. Please ensure 'India_block_wise_shape.shp' is in the app directory.")
    st.stop() # Stop the app if shapefile can't be loaded

states = ["Select State"] + sorted(list(set(shapefile["State"])))
state = st.selectbox("Select the state", states)

if not state == "Select State":
    districts = ["Select District"] + sorted(list(set(shapefile[shapefile["State"] == state]["District"])))
    district = st.selectbox("Select the district", districts)

    if not district == "Select District":
        col1, col2 = st.columns([1, 1])
        with col1:
            current_year = datetime.datetime.now().year
            start_year = st.number_input("Enter the Start date", min_value=2015, max_value=(current_year - 4))
        with col2:
            current_year = datetime.datetime.now().year
            end_year = st.number_input("Enter the end date", min_value=(start_year + 4), max_value=(current_year))

        if st.button("Run"):
            if not all([district, start_year, end_year]):
                st.warning("Please fill all the fields")
            else:
                try:
                    # Load service account info from Streamlit secrets
                    # It's assumed st.secrets["GCP_SERVICE_ACCOUNT"] is a dictionary (parsed JSON)
                    service_account_info = st.secrets["GCP_SERVICE_ACCOUNT"]

                    # Extract project_id from the service account info
                    project_id = service_account_info.get("project_id")
                    if not project_id:
                        st.error("Error: 'project_id' not found in your GCP_SERVICE_ACCOUNT secret. Please check your service account JSON.")
                        st.stop()

                    # Create credentials from the service account info
                    credentials = service_account.Credentials.from_service_account_info(service_account_info)

                    # Initialize Earth Engine with the credentials and the project ID
                    # This is the crucial change for the 'invalid_scope' error
                    ee.Initialize(credentials, project=project_id)
                    st.success(f"Earth Engine initialized successfully for project: {project_id}")

                    gdf = shapefile[shapefile["District"] == district]
                    region = gdf.to_json()
                    json_dict = json.loads(region)
                    aoi = ee.FeatureCollection(json_dict)

                    inputs = {
                        "project_id": project_id, # Ensure project_id is passed to trend_analysis
                        "years": [start_year, end_year],
                        "aoi": aoi
                    }

                    # Import get_trend after ee.Initialize to ensure EE is ready
                    from trend_analysis import get_trend

                    st.info("Calculating NDVI trend. This may take a moment...")
                    trend_map = get_trend(inputs)

                    Map = gmap.Map()
                    vis_params = {
                        'min': -0.05,
                        'max': 0.05,
                        'palette': ['red', 'white', 'green']
                    }

                    aoi_outline = aoi.style(**{
                        'color': 'blue',
                        'fillColor': '0000',
                        'width': 2
                    })
                    Map.addLayer(aoi_outline, {}, "Area of Interest")
                    Map.addLayer(trend_map, vis_params, "NDVI Trend Map")
                    Map.centerObject(aoi)
                    Map.to_streamlit()
                    st.success("NDVI Trend Map generated successfully!")

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.warning("Please ensure:")
                    st.warning("1. Your `GCP_SERVICE_ACCOUNT` secret in `.streamlit/secrets.toml` is a valid JSON string of your service account key.")
                    st.warning("2. The service account linked to the key has the 'Earth Engine User' role in your Google Cloud Project.")
                    st.warning("3. The Earth Engine API is enabled in your Google Cloud Project.")
                    st.warning(f"Project ID used: `{project_id if 'project_id' in locals() else 'Not found'}`")
