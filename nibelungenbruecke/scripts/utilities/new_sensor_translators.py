from os import PathLike
from typing import Union, Tuple

import pandas as pd
import json
import datetime

from nibelungenbruecke.scripts.utilities.BAM_Beispieldatensatz import load_bam
from nibelungenbruecke.scripts.utilities.BAM_Beispieldatensatz import save_bam


class Translator():
    
    def __init__(self, path_to_json:Union[str, bytes, PathLike], **kwargs):
        self.columns = ["Temp", "Move"]
        self.path_to_json = path_to_json
        self.kwargs = kwargs
        
    
    def _default_parameters(self):
        default_parameters_data = {
            "sensors": [
                {
                    "id": "DisplacementSensor",
                    "type": "DisplacementSensor",
                    "sensor_file": "displacement_sensor",
                    "units": "meter",
                    "dimensionality": "[length]",
                    "where": [1, 0.0, 0.0]
                }
            ]
        }
        return default_parameters_data
    
    def geodesic_to_cartesian(self, geodesic_coordinate):
        self.kwargs["origin_geodesic"]
        pass      
        
    def translator_to_sensor(self, df_output_path, meta_output_path):
        
        self.df, self.meta = load_bam(self.path_to_json, self.columns)

        if "Move" in self.meta.keys():
            sensor = self._default_parameters()                    

            if "coordinate" in self.meta["Move"].keys():
                sensor["sensors"][0]["where"] = self.meta["Move"]["coordinate"]  # geodesic_to_cartesian(dictionary[key][x])
                
            if "units" in self.meta["Move"].keys():
                sensor["sensors"][0]["units"] = self.meta["Move"]["units"]  
                
        
        with open(meta_output_path, "w") as f:
            json.dump(sensor, f, indent=4)
                
   
        df_dict = json.loads(self.df.to_json(orient='split'))
            
        with open(df_output_path, "w") as f:
            json.dump(df_dict, f)

        return df_output_path, meta_output_path
       
        
    def translator_to_MKP(self, sensor_obj) -> None:   
        self.df, self.meta = load_bam(self.path_to_json, self.columns)     
        movement = sensor_obj.sensors["DisplacementSensor"].data[0]
        for i in range(len(movement)):
            self.df["Move"][i] = movement[i]*1000

        self.meta["Move"]["coordinate"] = sensor_obj.sensors["DisplacementSensor"].where
        
        save_bam(self.df, self.meta)
