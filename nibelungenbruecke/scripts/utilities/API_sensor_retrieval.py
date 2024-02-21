 
#%%
# Importieren der erforderlichen Bibliotheken
import requests
import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

import numpy as np
import json
import h5py



class API_Request:
    
    def __init__(self):
        
        # /samples API-Endpunkt 
        self.url = "https://func-70021-nibelungen-export.azurewebsites.net/samples"
 
        self.headers = {
            "Content-Type": "application/json"
            }
 
        # url parameter 
        self.params = {
            "code": "nv8QrKftsTHj93hPM4-BiaJJYbWU7blfUGz89KdkuEbpAzFuHX1Rmg==" # der Code aus den über Keeper mitgetielten Zugangdaten 
        }

        #self.start_time = datetime.strptime("2023-08-11T08:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        #self.end_time = datetime.strptime("2023-08-11T08:01:00Z", "%Y-%m-%dT%H:%M:%SZ")
        
           
        self.body = {
            "startTime": "2023-08-11T08:00:00Z",
            "endTime": "2023-09-11T08:01:00Z",
            "meta_channel": True,
            "columns": ['E_plus_445LVU_HS--o-_Avg1',
             'E_plus_445LVU_HS--u-_Avg1',
             'E_plus_413TU_HSS-m-_Avg1',
             ]
            }
        
        
        """
        self.body = {
            "startTime": "2023-08-11T08:00:00Z",
            "endTime": "2023-09-11T08:01:00Z",
            "meta_channel": True,
            "columns": ['E_plus_413TU_HS--o-_Avg1',
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
       
    def API(self): 
        
        # Senden der POST-Anfrage
        response = requests.post(self.url, headers=self.headers, params=self.params, json=self.body)
         
        # Überprüfen, ob die Anfrage erfolgreich war
        if response.status_code != 200:
            raise ValueError(f"Anfrage fehlgeschlagen mit Statuscode {response.status_code}: {response.text}")
         
        # Daten aus der Antwort extrahieren 
        data = response.json()
         
        # in einen DataFrame laden
        self.df = pd.DataFrame(data["rows"], columns=[col["ColumnName"] for col in data["columns"]])
         
        # Optional: Timestamp-Spalte konvertieren und als Index setzen
        #self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], format="ISO8601")
        self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"])
        self.df = self.df.set_index("Timestamp")
         
        # Aufgrund unterschiedlicher Abtastraten der Sensoren enthält DataFrame NaN-Werte
        # print(self.df)
        return pd.DataFrame(self.df[self.df.columns], index=pd.to_datetime(self.df.index))

# %%
    
from os import PathLike
from typing import Union, Tuple

import pandas as pd
import json
import datetime
import h5py
from datetime import datetime, timedelta

class saveAPI:
    
    def __init__(self, path_meta, df, path_df):

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
        
        self.path_meta = path_meta
        self.path_df = path_df
        
        self.df = df
         
    def save(self):

        # Origin: "49.630742, 8.378049"
        
        for i in range(len(self.df.columns)):
            if self.df.columns[i] == 'E_plus_413TU_HS--o-_Avg1':
                
                column_name = self.df.columns[i]
                    
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [44.4925, 4.74, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_413TU_HSS-m-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [44.4925, 3.69, 0.0],
                "height": 105                       
            })

            elif self.df.columns[i] == 'E_plus_413TU_HS--u-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [44.4925, 2.29, 0.0],
                "height": 106                         
            })
                
            elif self.df.columns[i] == 'E_plus_423NU_HSN-o-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [45.3425, 5.54, 0.0],
                "height": 107                          
            })
            
            elif self.df.columns[i] == 'E_plus_040TU_HS--o-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 4.74, 0.0],
                "height": 108                         
            })

            elif self.df.columns[i] == 'E_plus_040TU_HSN-m-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 2.37, 0.005],
                "height": 109                         
            })

            elif self.df.columns[i] == 'E_plus_040TU_HSS-m-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [0.92, 2.37, 0.005],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_040TU_HS--u-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.355],
                "height": 104.105                       
            })
            
            elif self.df.columns[i] == 'E_plus_413TI_HSS-m-_Avg':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_040TI_HSS-u-_Avg':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_423NUT_HSN-o-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [45.3425, 4.34, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_467NUT_HSN-o_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [49.8925, 4.34, 0.0],
                "height": 104.105                       
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

            elif self.df.columns[i] == 'E_plus_445LVU_HS--o-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [47.5925, 4.74, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_445LVU_HS--u-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [47.5925, 0.0, 0.0],
                "height": 104.105                       
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
  
from os import PathLike
from typing import Union, Tuple
import pandas as pd
import json
import datetime
import csv
from math import atan2, cos, sin, sqrt, radians, degrees

class Translator:
    
    def __init__(self, meta_path: Union[str, bytes, PathLike], **kwargs):
        self.columns = ["Temp", "Move", "Humidity"]
        self.meta_path = meta_path
        self.kwargs = kwargs
    
    def _default_parameters(self):
        return {
            "sensors": []
        }

    def translator_to_sensor(self, meta_output_path):
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
                        "where": item["coordinate"]
                    }

                    if key == "Temp":
                        sensor_data["type"] = "TemperatureSensor"
                        sensor_data["sensor_file"] = "temperature_sensor"
                        sensor_data["units"] = "kelvin"
                
                    elif key == "Move":
                        sensor_data["type"] = "DisplacementSensor"
                        sensor_data["sensor_file"] = "displacement_sensor"
                
                    default_parameters_data["sensors"].append(sensor_data)
                
        with open(meta_output_path, "w") as f:
            json.dump(default_parameters_data, f, indent=4)

        return meta_output_path
    
    def save_displacement_values(self, path, disp_values):
        """
        Save displacement values corresponding to each sensor ID in the MKP_meta_output_path JSON file.

        Parameters:
            disp_values: Displacement values.
        """
        self.path = path
        with open(self.path["MKP_meta_output_path"], 'r') as f:
            metadata = json.load(f)

        virtual_sensors = []
        for sensor in metadata["sensors"]:
            sensor_id = sensor["id"]
            position = sensor["where"]
            displacement_value = disp_values.sensors.get(sensor_id, None)
            if displacement_value is not None:
                displacement_value_list = displacement_value.data[0].tolist()  # Convert ndarray to list
                virtual_sensors.append({"id": sensor_id, "displacement": displacement_value_list})

        metadata["virtual_sensors"] = virtual_sensors

        with open(self.path["MKP_meta_output_path"], 'w') as f:
            json.dump(metadata, f, indent=4)

    @staticmethod
    def cartesian_to_geodesic(cartesian_coord, origin=(49.630742, 8.378049)):
        origin_lat, origin_lon = radians(origin[0]), radians(origin[1])

        x, y, z = cartesian_coord
        distance = sqrt(x**2 + y**2 + z**2)
        geod_lat = atan2(z, sqrt(x**2 + y**2))
        geod_lon = atan2(y, x)

        geod_lat = degrees(geod_lat)
        geod_lon = degrees(geod_lon)

        geod_lon = (geod_lon + 540) % 360 - 180

        geod_lat += origin_lat
        geod_lon += origin_lon

        return [geod_lat, geod_lon, distance]

        """
        utm_zone = int((geod_lon + 180) / 6) + 1  # Determine UTM zone
        utm_band = 'C' if 56 > geod_lat > 0 else 'D'  # Determine UTM band

        utm_proj = Proj(proj='utm', zone=utm_zone, ellps='WGS84', datum='WGS84', south=False)
        utm_x, utm_y = utm_proj(geod_lon, geod_lat)

        return [utm_x, utm_y, distance, utm_zone, utm_band]
        """
            
    def save_to_MKP(self, df, displacement_meta_path, output_path):

        # Create a dictionary representing the JSON structure
        json_data = {
            "df": {
                "columns": df.columns.tolist(),
                "index": df.index.strftime("%Y-%m-%dT%H:%M:%S.000000Z").tolist(),
                "data": df.values.tolist()
            },
            "meta": {}
        }

        # Load displacement metadata
        with open(displacement_meta_path["MKP_meta_output_path"], "r") as file:
            displacement_data = json.load(file)

        for column in df.columns:
            sensor_coords = next((sensor["where"] for sensor in displacement_data["sensors"] if sensor["id"] == column), "")
            geod_coords = self.cartesian_to_geodesic(sensor_coords) if sensor_coords else ""
            json_data["meta"][column] = {
                "name": column,
                "unit": "\u00b0C",  
                "sample_rate": 0.0016666666666666668,
                "coordinate": geod_coords,
                "height": "" 
            }

        with open(output_path, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

    def save_VS(self, path, path_02, displacement_values):
        """
        Save displacement values corresponding to each sensor ID in the MKP_meta_output_path JSON file.

        Parameters:
            displacement_values: Displacement values.
        """
        with open(path["MKP_meta_output_path"], 'r') as f:
            metadata = json.load(f)

        with open(path_02, 'r') as f:
            MKP_data = json.load(f)
        
        # Check if "additional_data" already exists, if not, create it
        if "additional_data" not in MKP_data:
            MKP_data["additional_data"] = {"virtual_sensors": {}}
        
        additional_data = MKP_data["additional_data"]["virtual_sensors"]

        for sensor in metadata["sensors"]:
            sensor_id = sensor["id"]
            position = sensor["where"]
            displacement_value = displacement_values.sensors.get(sensor_id, None)
            if displacement_value is not None:
                displacement_value_list = displacement_value.data[0].tolist()  # Convert ndarray to list
                if sensor_id not in additional_data:
                    additional_data[sensor_id] = {"displacements": []}
                # Append the new displacement values list to the existing "displacements" array
                additional_data[sensor_id]["displacements"].append(displacement_value_list)

        with open(path_02, 'w') as f:
            json.dump(MKP_data, f, indent=4)
