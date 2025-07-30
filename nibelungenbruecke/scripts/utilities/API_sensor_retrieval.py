# Importieren der erforderlichen Bibliotheken
import requests
import pandas as pd
from datetime import datetime, timedelta
from os import PathLike
from typing import Union, Tuple
import matplotlib.pyplot as plt
import numpy as np
import json
import h5py
import math
from pyproj import Proj, transform
from nibelungenbruecke.scripts.utilities.mesh_point_detector import query_point


class API_Request:
    """
    A class to handle API requests.

    Attributes:
        url: The API endpoint URL.
        headers: Request headers.
        params: URL parameters.
        body: Request body parameters.
    """
    
    def __init__(self, api_key, start_time, end_time, time_step):      ##TODO: time step !!!
        self.url = "https://func-70021-nibelungen-export.azurewebsites.net/samples"
        self.headers = {
            "Content-Type": "application/json"
        }
# =============================================================================
#         if secrets_location == "":
#             while True:
#                 print("Connecting to sensor database...")
#                 secret_code = input("\nEnter the code to connect API: ").strip()
#                 if secret_code:
#                     self.params = {"code": secret_code}
#                     break
#                 else:
#                     print("Secret code cannot be empty. Please try again.")
#         else:
#             with open(secrets_location) as f:
#                 self.params = {"code": f.read().strip()}
# =============================================================================
        self.params = {"code": api_key}
        start_time = start_time
        if not start_time:
            start_time = datetime.utcnow()

        end_time = end_time
        if not end_time:
            end_time = start_time + timedelta(days=5)  

        #print(f"Time window:\n  Start: {start_time.isoformat()[:10]}\n  End:   {end_time.isoformat()[:10]}")
        
        self.body = {
            "startTime": start_time,
            "endTime": end_time,
            "meta_channel": True,
            "columns": ["F_plus_000TA_KaS-o-_Avg1",
                        "F_plus_000S_KaS-o-_Avg1",
                        "E_plus_040TI_HSS-u-_Avg",
                        "E_plus_040TU_HS--o-_Avg1",
                        "E_plus_040TU_HSN-m-_Avg1",
                        "E_plus_040TU_HSS-m-_Avg1",
                        "E_plus_040TU_HS--u-_Avg1",
                        ]
            }
        
        # Body for requesting data of all the sensors
        """
        self.body = {
            "startTime": "2023-08-11T08:00:00Z",
            "endTime": "2023-09-11T08:01:00Z",
            "meta_channel": True,
            "columns": [   
            "F_plus_000TA_KaS-o-_Avg1", 
            "F_plus_000S_KaS-o-_Avg1", 
            "E_plus_040TU_HS--u-_Avg1", 
            "E_plus_040TI_HSS-u-_Avg",
            "E_plus_080DU_HSN-u-_Avg1"
            'E_plus_413TU_HS--o-_Avg1',
         
                
             'E_plus_413TU_HSN-m-_Avg1',
             'E_plus_413TU_HSS-m-_Avg1',
             'E_plus_413TU_HS--u-_Avg1',
             'E_plus_423NU_HSN-o-_Avg1',
             'E_plus_423NUT_HSN-o-_Avg1',
             'E_plus_445LVU_HS--o-_Avg1',
             'E_plus_445LVU_HS--u-_Avg1',
             'E_plus_467NU_HSN-o-_Avg1',
             'E_plus_467NUT_HSN-o_Avg1',
             'F_plus_000TA_KaS-o-_Avg1',
             'F_plus_000S_KaS-o-_Avg1',
             'F_plus_000N_KaS-o-_Avg1',
             'E_plus_040TU_HS--o-_Avg1',
             'E_plus_040TU_HSN-m-_Avg1',
             'E_plus_040TU_HSS-m-_Avg1',
             'E_plus_040TU_HS--u-_Avg1',
             'E_plus_080DU_HSN-o-_Avg1',
             'E_plus_080DU_HSN-u-_Avg1',
             'E_plus_413TI_HSS-m-_Avg',
             'E_plus_040TI_HSS-u-_Avg',
             'E_plus_233BU_HSN-m-_Avg1',
             'E_plus_432BU_HSN-m-_Avg1']
            }
        """

        # Sensors
        """
        TU: Temperaturmessung des Überbaus
        LI: Luftfeuchtigkeit im Inneren des Hohlkastens
        TI: Temperatur im Inneren des Hohlkastens
        NU: Neigung des Überbaus
        NUT: Temperatur Neigungsaufnehmer
        LVU: Längsverschiebung des Überbaus
        TA: Außentemperaturmessung
        LA: Luftfeuchtigkeit außen
        S: Strahlungsintensität
        N: Niederschlag
        DU: Dehnung des Überbaus        
        
        """
            
            
        """
        All mesaurements with 10 hz
        
        ["E_plus_413TU_HS--o-","E_plus_413TU_HS--o-_Avg1","E_plus_413TU_HS--o-_Max1",
        "E_plus_413TU_HS--o-_Min1","E_plus_413TU_HSN-m-","E_plus_413TU_HSN-m-_Avg1",
        "E_plus_413TU_HSN-m-_Max1","E_plus_413TU_HSN-m-_Min1","E_plus_413TU_HSS-m-",
        "E_plus_413TU_HSS-m-_Avg1","E_plus_413TU_HSS-m-_Max1","E_plus_413TU_HSS-m-_Min1",
        "E_plus_413TU_HS--u-","E_plus_413TU_HS--u-_Avg1","E_plus_413TU_HS--u-_Max1",
        "E_plus_413TU_HS--u-_Min1","E_plus_423NU_HSN-o-","E_plus_423NU_HSN-o-_Avg1",
        "E_plus_423NU_HSN-o-_Max1","E_plus_423NU_HSN-o-_Min1","E_plus_423NUT_HSN-o-",
        "E_plus_423NUT_HSN-o-_Avg1","E_plus_423NUT_HSN-o-_Max1","E_plus_423NUT_HSN-o-_Min1",
        "E_plus_445LVU_HS--o-","E_plus_445LVU_HS--o-_Avg1","E_plus_445LVU_HS--o-_Max1",
        "E_plus_445LVU_HS--o-_Min1","E_plus_445LVU_HS--u-","E_plus_445LVU_HS--u-_Avg1",
        "E_plus_445LVU_HS--u-_Max1","E_plus_445LVU_HS--u-_Min1","E_plus_467NU_HSN-o-",
        "E_plus_467NU_HSN-o-_Avg1","E_plus_467NU_HSN-o-_Max1","E_plus_467NU_HSN-o-_Min1",
        "E_plus_467NUT_HSN-o","E_plus_467NUT_HSN-o_Avg1","E_plus_467NUT_HSN-o_Max1",
        "E_plus_467NUT_HSN-o_Min1","F_plus_000TA_KaS-o-","F_plus_000TA_KaS-o-_Avg1",
        "F_plus_000TA_KaS-o-_Max1","F_plus_000TA_KaS-o-_Min1","F_plus_000LA_KaS-o-",
        "F_plus_000LA_KaS-o-_Avg1","F_plus_000LA_KaS-o-_Max1","F_plus_000LA_KaS-o-_Min1",
        "F_plus_000S_KaS-o-","F_plus_000S_KaS-o-_Avg1","F_plus_000S_KaS-o-_Max1",
        "F_plus_000S_KaS-o-_Min1","F_plus_000N_KaS-o-","F_plus_000N_KaS-o-_Avg1",
        "F_plus_000N_KaS-o-_Max1","F_plus_000N_KaS-o-_Min1","E_plus_040TU_HS--o-",
        "E_plus_040TU_HS--o-_Avg1","E_plus_040TU_HS--o-_Max1","E_plus_040TU_HS--o-_Min1",
        "E_plus_040TU_HSN-m-","E_plus_040TU_HSN-m-_Avg1","E_plus_040TU_HSN-m-_Max1",
        "E_plus_040TU_HSN-m-_Min1","E_plus_040TU_HSS-m-","E_plus_040TU_HSS-m-_Avg1",
        "E_plus_040TU_HSS-m-_Max1","E_plus_040TU_HSS-m-_Min1","E_plus_040TU_HS--u-",
        "E_plus_040TU_HS--u-_Avg1","E_plus_040TU_HS--u-_Max1","E_plus_040TU_HS--u-_Min1",
        "E_plus_080DU_HSN-o-","E_plus_080DU_HSN-o-_Avg1","E_plus_080DU_HSN-o-_Max1",
        "E_plus_080DU_HSN-o-_Min1","E_plus_080DU_HSN-u-","E_plus_080DU_HSN-u-_Avg1",
        "E_plus_080DU_HSN-u-_Max1","E_plus_080DU_HSN-u-_Min1","E_plus_413LI_HSS-m-",
        "E_plus_413LI_HSS-m-_Avg","E_plus_413LI_HSS-m-_Max","E_plus_413LI_HSS-m-_Min",
        "E_plus_040LI_HSS-u-","E_plus_040LI_HSS-u-_Avg","E_plus_040LI_HSS-u-_Max",
        "E_plus_040LI_HSS-u-_Min","E_plus_413TI_HSS-m-","E_plus_413TI_HSS-m-_Avg",
        "E_plus_413TI_HSS-m-_Max","E_plus_413TI_HSS-m-_Min","E_plus_040TI_HSS-u-",
        "E_plus_040TI_HSS-u-_Avg","E_plus_040TI_HSS-u-_Max","E_plus_040TI_HSS-u-_Min",
        "E_plus_233BU_HSN-m-_Avg1","E_plus_233BU_HSN-m-_Max1","E_plus_233BU_HSN-m-_Min1",
        "E_plus_432BU_HSN-m-_Avg1","E_plus_432BU_HSN-m-_Max1","E_plus_432BU_HSN-m-_Min1"]
        """
       
    
    def Plotting(self):
        
        # Plotting each column separately
        for column in self.df.columns:
            plt.plot(self.df.index, self.df[column], label=column)

            plt.xlabel('Timestamp')
            plt.ylabel('Values')
            plt.title('Time Series Data')

            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.show()
       
    def fetch_data(self):
        """
        Fetch data from the API and store it in a DataFrame.
        """

        response = requests.post(self.url, headers=self.headers, params=self.params, json=self.body)

        if response.status_code != 200:
            raise ValueError(f"Anfrage fehlgeschlagen mit Statuscode {response.status_code}: {response.text}")
        data = response.json()
        self.df = pd.DataFrame(data["rows"], columns=[col["ColumnName"] for col in data["columns"]])
        #self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], format="ISO8601")
        #format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], format='ISO8601', utc=True)
        self.df = self.df.set_index("Timestamp")
        # print(self.df)
        return pd.DataFrame(self.df[self.df.columns], index=pd.to_datetime(self.df.index))

# %%
class MetadataSaver:
    
    def __init__(self, path, df):
        self.data = {
            "df": {
                "columns": [],
                "index": [],
                "data": []
            },
            "meta": {
                "Temp": [],
                "Move": [],
                "Humidity": []
            }
        }
        self.path_meta = path["meta_output_path"]
        self.path_df = path["df_output_path"]
        self.df = df
         
    def saving_metadata(self):

        # Origin: "49.630742, 8.378049"
        for i in range(len(self.df.columns)):
            if self.df.columns[i] == 'E_plus_413TU_HS--o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [41.42, 0.0, 0.0],
                "height": 107.438                        
            })

            elif self.df.columns[i] == 'E_plus_413TU_HSS-m-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [41.42, -3.69, 0.0],
                "height": 103.748                      
            })

            elif self.df.columns[i] == 'E_plus_413TU_HS--u-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [41.42, -4.74, 0.0],
                "height": 102.698                        
            })
                
            elif self.df.columns[i] == 'E_plus_423NU_HSN-o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [42.22, -3.33, 0.0],
                "height": 102.698                          
            })
            
            elif self.df.columns[i] == 'E_plus_040TU_HS--o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [4, 0.0, 0.0],
                "height": 107.438                         
            })

            elif self.df.columns[i] == 'E_plus_040TU_HSN-m-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [4, -2.37, 0.005],
                "height": 105.068                        
            })

            elif self.df.columns[i] == 'E_plus_040TU_HSS-m-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [4, -2.37, 0.005],
                "height": 105.068                       
            })

            elif self.df.columns[i] == 'E_plus_040TU_HS--u-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [4, -4.74, 0.355],
                "height": 102.698                      
            })
            
            elif self.df.columns[i] == 'E_plus_413TI_HSS-m-_Avg':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [41.42, -3.33, 0.0],
                "height": 102.698                       
            })

            elif self.df.columns[i] == 'E_plus_040TI_HSS-u-_Avg':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [4, -4.74, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_423NUT_HSN-o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [42.22, 0.0, 0.0],
                "height": 107.438                       
            })

            elif self.df.columns[i] == 'E_plus_467NUT_HSN-o_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [46.82, 0.0, 0.0],
                "height": 107.438                       
            })

            elif self.df.columns[i] == 'F_plus_000TA_KaS-o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })
                
            elif self.df.columns[i] == 'F_plus_000S_KaS-o-_Avg1':   ##TODO: copy and pasted from another sensor!! Not correct, check the plan!
                column_name = self.df.columns[i]
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
                "height": 107.438                       
            })

            elif self.df.columns[i] == 'E_plus_445LVU_HS--o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [44.52, 0.0, 0.0],
                "height": 107.438                       
            })

            elif self.df.columns[i] == 'E_plus_445LVU_HS--u-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [44.52, 0.0, 0.0],
                "height": 102.698                       
            })
            
            elif self.df.columns[i] == 'E_plus_080DU_HSN-o-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [80.0, 0.0, 0.0],
                "height": 107.438                        
            })
                
            elif self.df.columns[i] == 'E_plus_080DU_HSN-u-_Avg1':
                column_name = self.df.columns[i]
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [80.0, -4.74, 0.0],
                "height": 102.698                       
            })

        with open(self.path_meta, "w") as json_file:
            json.dump(self.data, json_file, indent=2)
            
        # Saving dataframe of the request
        #self.df.to_hdf(self.path_df, key='e',  mode='w')
        
        # Saving dataframe of the request as CSV
        self.df.to_csv(self.path_df, index=True)
            
        # Saving dataframe of the request as json
        #self.df.to_json(self.path_df)
        
        #print(self.data)
        return self.path_meta, self.path_df
    
# %%
class Translator:
    
    def __init__(self, path, **kwargs):
        self.columns = ["Temp", "Move", "Humidity"]
        self.path = path
        self.meta_path = self.path["meta_output_path"]
        self.kwargs = kwargs

    def _default_parameters(self):
        return {
            "sensors": []
        }

    def translator_to_sensor(self, mesh):
        self.MKP_meta_output_path = self.path["MKP_meta_output_path"]

        default_parameters_data = self._default_parameters()
        with open(self.meta_path, 'r') as f:
            self.j = json.load(f)    
        self.meta = self.j["meta"]

        for key in self.columns:
            if key in self.meta.keys():
                for item in self.meta[key]:
                    sensor_data = {
                        "id": item["name"],
                        "type": "",
                        "sensor_file": "",
                        "units": "meter",
                        "dimensionality": "[length]",
                        "where": query_point(item["coordinate"], mesh)[0].tolist()  ##TODO: error causing the same results for vs !
                    }

                    if key == "Temp":
                        sensor_data["type"] = "TemperatureSensor"
                        sensor_data["sensor_file"] = "temperature_sensor"
                        sensor_data["units"] = "kelvin"
                        sensor_data["dimensionality"] = "[temperature]"
                
                    elif key == "Move":
                        sensor_data["type"] = "DisplacementSensor"
                        sensor_data["sensor_file"] = "displacement_sensor"
                
                    default_parameters_data["sensors"].append(sensor_data)
                    
        for i in ["Sensor_u", "Sensor_o", "Sensor_n", "Sensor_s"]:
            sensor_data = {
            "id": i,
            "type": "TemperatureSensor",
            "sensor_file": "temperature_sensor",
            "units": "kelvin",
            "dimensionality": "[temperature]",
            "where": [0, 0, 0],
            }
            
            default_parameters_data["sensors"].append(sensor_data)

        with open(self.MKP_meta_output_path, "w") as f:
            json.dump(default_parameters_data, f, indent=4)

        return self.MKP_meta_output_path

    @staticmethod
    def cartesian_to_geodesic(cartesian, origin=[49.630742, 8.378049]):
        # Define the Earth's radius in kilometers
        R = 6371.0

        # Convert origin to radians
        origin_lat_rad = math.radians(origin[0])
        origin_lon_rad = math.radians(origin[1])

        # Convert Cartesian coordinates to geodesic
        x, y, z = cartesian
        distance = math.sqrt(x**2 + y**2 + z**2)
        
        # Calculate latitude
        latitude = math.asin(math.sin(origin_lat_rad) * math.cos(distance / R) +
                            math.cos(origin_lat_rad) * math.sin(distance / R) * math.cos(0))

        # Calculate longitude
        longitude = origin_lon_rad + math.atan2(math.sin(0) * math.sin(distance / R) * math.cos(origin_lat_rad),
                                                math.cos(distance / R) - math.sin(origin_lat_rad) * math.sin(latitude))

        # Convert latitude and longitude to degrees
        latitude = math.degrees(latitude)
        longitude = math.degrees(longitude)

        return latitude, longitude
    
    @staticmethod
    def geodesic_to_utm(latitude, longitude):
        # Define the UTM projection using WGS84 datum
        utm_zone_number = math.floor((longitude + 180) / 6) + 1
        utm_zone_letter = 'C' if -80 <= latitude < 72 else 'D'
        utm_proj = Proj(proj='utm', zone=utm_zone_number, ellps='WGS84')

        # Convert latitude and longitude to UTM coordinates
        utm_easting, utm_northing = utm_proj(longitude, latitude)

        # Format UTM coordinates
        utm_easting_str = "{:.0f}".format(utm_easting)
        utm_northing_str = "{:.0f}".format(utm_northing)

        return f"{utm_zone_number} {utm_zone_letter} E{utm_easting_str} N{utm_northing_str}"
    
    def save_to_MKP(self, df):
        self.MKP_input_path = self.path["MKP_meta_output_path"]
        self.translated_data_path = self.path["MKP_translated_output_path"]
        
        json_data = {
            "df": {
                "columns": df.columns.tolist(),
                "index": df.index.strftime("%Y-%m-%dT%H:%M:%S.000000Z").tolist(),
                "data": df.values.tolist()
            },
            "meta": {}
        }

        with open(self.MKP_input_path, "r") as file:
            self.displacement_data = json.load(file)

        for column in df.columns:
            sensor_coords = next((sensor["where"] for sensor in self.displacement_data["sensors"] if sensor["id"] == column), "")
            geod_coords = self.cartesian_to_geodesic(sensor_coords) if sensor_coords else ""
            utm_coords = self.geodesic_to_utm(*geod_coords)
            json_data["meta"][column] = {
                "name": column,
                "unit": "\u00b0C",  
                "sample_rate": 0.0016666666666666668,
                "coordinate": utm_coords,
                "height": "" 
            }

        with open(self.translated_data_path, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

    def save_virtual_sensor(self, problem):
        self.virtual_sensor_added_output_path = self.path["virtual_sensor_added_output_path"]

        with open(self.MKP_input_path, 'r') as f:
            self.metadata = json.load(f)

        with open(self.translated_data_path, 'r') as f:
            MKP_data = json.load(f)
        try:    
            with open(self.virtual_sensor_added_output_path, 'r') as f:
                VS_data = json.load(f)
        except:
            VS_data = MKP_data
            
        if "virtual_sensors" not in VS_data:
            VS_data["virtual_sensors"] = {}

        for sensor in self.metadata["sensors"]:
            sensor_id = sensor["id"]
            position = sensor["where"]
            if sensor_id in ["E_plus_080DU_HSN-u-_Avg1"]:       ##TODO: To be extended to include other displacement realted sensors!!
                displacement_value = problem.sensors.get(sensor_id, None)
                if displacement_value is not None:
                    displacement_value_list = displacement_value.data[-1].tolist()
                    if sensor_id not in VS_data["virtual_sensors"]:
                        VS_data["virtual_sensors"][sensor_id] = {"displacements": []}
                    VS_data["virtual_sensors"][sensor_id]["displacements"].append(displacement_value_list)

        with open(self.virtual_sensor_added_output_path, 'w') as f:
            json.dump(VS_data, f, indent=4)