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