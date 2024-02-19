 
#%%
# Importieren der erforderlichen Bibliotheken
import requests
import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

import numpy as np
import json
import h5py



class API_request:
    
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
        
        """    
        self.body = {
            "startTime": "2023-08-11T08:00:00Z",
            "endTime": "2023-09-11T08:01:00Z",
            "meta_channel": True,
            "columns": ['E_plus_445LVU_HS--o-_Avg1',
             'E_plus_445LVU_HS--u-_Avg1',
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

# from nibelungenbruecke.scripts.utilities.BAM_Beispieldatensatz import load_bam
# from nibelungenbruecke.scripts.utilities.BAM_Beispieldatensatz import save_bam

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
                "coordinate": [1, 0.0, 1.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_413TU_HSS-m-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 1.1],
                "height": 105                       
            })

            elif self.df.columns[i] == 'E_plus_413TU_HS--u-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 1.2],
                "height": 106                         
            })
                
            elif self.df.columns[i] == 'E_plus_423NU_HSN-o-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 1.3],
                "height": 107                          
            })
            
            elif self.df.columns[i] == 'E_plus_040TU_HS--o-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 1.4],
                "height": 108                         
            })

            elif self.df.columns[i] == 'E_plus_040TU_HSN-m-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 1.5],
                "height": 109                         
            })

            elif self.df.columns[i] == 'E_plus_040TU_HSS-m-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_040TU_HS--u-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
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
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_467NUT_HSN-o_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Temp"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
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
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })

            elif self.df.columns[i] == 'E_plus_445LVU_HS--u-_Avg1':

                column_name = self.df.columns[i]
                
                self.data["meta"]["Move"].append({
                "name": column_name,
                "unit": "\u00b0C",
                "sample_rate": 0.0016666666666666668,   
                "coordinate": [1, 0.0, 0.0],
                "height": 104.105                       
            })

        
        with open(self.path_meta, "w") as json_file:
            json.dump(self.data, json_file, indent=2)
            
        # Saving dataframe of the request
        #self.df.to_hdf(self.path_df, key='e',  mode='w')
        
        # Saving dataframe of the request as CSV
        self.df.to_csv(self.path_df, index=False)
        
        
        #print(self.data)
        return self.path_meta, self.path_df
    
# %%
  
from os import PathLike
from typing import Union, Tuple
import pandas as pd
import json
import datetime


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