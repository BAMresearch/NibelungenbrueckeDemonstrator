import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta

class OpenMeteo:
    
    def __init__(self, start_time, end_time, time_step="1h"):
        # Setup the Open-Meteo API client with cache and retry on error
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)
        
        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
        	"latitude": 52.52,
        	"longitude": 13.41,
        	"start_date": "2026-01-21",
        	"end_date": "2026-02-04",
        	"hourly": ["temperature_2m", "shortwave_radiation_instant", "shortwave_radiation"],
        }
        
        # Nibelungenbrücke coords
        latitude = 49.6311231
        longitude = 8.3799384
        
        #params["start_date"] = start_time
        dt = datetime.strptime(start_time, "%Y-%m-%d")
        dt_minus_3_weeks = dt - timedelta(weeks=3)
        new_start_time = dt_minus_3_weeks.strftime("%Y-%m-%d")
        
        params["start_date"] = new_start_time
        params["end_date"] = end_time
        params["latitude"] = latitude
        params["longitude"] = longitude
        
        
        responses = openmeteo.weather_api(url, params=params)
        
        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        #print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
        #print(f"Elevation: {response.Elevation()} m asl")
        #print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
        
        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_shortwave_radiation_instant = hourly.Variables(1).ValuesAsNumpy()
        hourly_shortwave_radiation = hourly.Variables(2).ValuesAsNumpy()
        
        hourly_data = {"date": pd.date_range(
        	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        	end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        	freq = pd.Timedelta(seconds = hourly.Interval()),
        	inclusive = "left"
        )}
        
        hourly_data["air_temperature"] = hourly_temperature_2m
        hourly_data["shortwave_radiation"] = hourly_shortwave_radiation_instant ##TODO: Not relevant!
        hourly_data["shortwave_irradiation"] = hourly_shortwave_radiation
        
        hourly_dataframe = pd.DataFrame(data = hourly_data)
        #print("\nHourly data\n", hourly_dataframe)
        
        self.result = self.frequency_manage(hourly_dataframe, time_step)
        
        print("Filtered data for specified frequency")
        #print(self.result)
        #return result
    
    
    def frequency_manage(self, OM_dataframe, freq="1h"):
        OM_dataframe["date"] = pd.to_datetime(OM_dataframe["date"])
        df = OM_dataframe.set_index("date")
        df_filtered = df.resample(freq).interpolate()
        
        return df_filtered
        

if __name__ == "__main__":

    start_time = '2024-08-11'
    end_time = '2024-09-13'
    
    
    OM = OpenMeteo(start_time, end_time, '100min')
    df = OM.result