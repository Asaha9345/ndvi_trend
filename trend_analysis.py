import ee
import geemap
import geopandas as gpd
import json

# inputs = {"project_id":"ee-akashsaha6660",
#           "years":[2018,2024],
#           "aoi": "FeatureCollection"}

def get_trend(inputs):
    def get_images(years, roi):
        start_year = years[0]
        end_year = years[1]
        image_list = []
        for year in range(start_year,(end_year+1)):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                    .filterBounds(roi)
                    .filterDate(start_date, end_date)
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',5)))
            if collection.size().getInfo()>0:
                image = (collection.median()
                        .clip(roi)
                        .select("B2","B3","B4","B8")
                        .divide(10000)
                        .set('year',year))
                image_list.append(image)
            else:
                print(f"No valid image found for {start_date} to {end_date}")
        
        return image_list
    
    all_images = get_images(inputs["years"],inputs["aoi"])

    def compute_ndvi(image):
        ndvi = image.normalizedDifference(["B8","B4"]).rename("NDVI")
        return image.addBands(ndvi).set('year', image.get('year'))

    ndvi_images = [compute_ndvi(image) for image in all_images]


    def add_time_band(image):
        year = ee.Number(image.get('year')).float()
        time_band = ee.Image.constant(year).rename('time').toFloat()
        return image.addBands(time_band.clip(inputs["aoi"]))


    ndvi_images = [add_time_band(img.select('NDVI')) for img in ndvi_images]
    ndvi_collection = ee.ImageCollection(ndvi_images)

    # Linear regression of NDVI over time
    trend = ndvi_collection.select(['time', 'NDVI']).reduce(ee.Reducer.linearFit())
    return trend.select('scale')