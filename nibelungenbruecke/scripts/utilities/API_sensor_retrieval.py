 
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
