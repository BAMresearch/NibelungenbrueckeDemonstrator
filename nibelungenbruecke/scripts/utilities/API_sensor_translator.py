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
                
                    elif key == "Move":
                        sensor_data["type"] = "DisplacementSensor"
                        sensor_data["sensor_file"] = "displacement_sensor"
                
                    default_parameters_data["sensors"].append(sensor_data)
                
        with open(meta_output_path, "w") as f:
            json.dump(default_parameters_data, f, indent=4)

        return meta_output_path