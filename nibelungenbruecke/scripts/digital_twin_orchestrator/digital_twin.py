import sys
import json
import copy
import pickle
import importlib
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator_cache import ObjectCache

class DigitalTwin:
    def __init__(self, model_path: str, model_parameters: dict, dt_path: str, model_to_run = "Displacement_1"):
        self.model_path = model_path
        self.model_parameters = model_parameters
        self.dt_path = dt_path
        self.model_to_run = model_to_run
        self.load_models()
        self.cache_object = ObjectCache()
               
    def load_models(self):
        with open(self.dt_path, 'r') as json_file:
            self.models = json.load(json_file)
        
    def set_model(self):
        for model_info in self.models:
            if model_info["name"] == self.model_to_run:
                self.cache_model_name = model_info["type"]
                self.cache_object_name = model_info["class"]
                rel_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/"
                self.cache_model_path = rel_path + model_info["path"]
                return True
        raise ValueError(f"'{self.model_to_run}' not found in the defined models.")
        
        
    def store_update(self):            
        measured_vs_path = self.model_parameters["virtual_sensor_added_output_path"]
        with open(measured_vs_path, 'r') as f:
            sensor_measurement = json.load(f)
            
        triggered = False    
        for i in sensor_measurement["virtual_sensors"].keys():
            if sensor_measurement["virtual_sensors"][i]["displacements"][-1] == sensor_measurement["virtual_sensors"][i]["displacements"][-2]:
                triggered = False
            else:
                triggered = True
                
        return triggered
            
    def predict(self, input_value):      
        if self.set_model():
            
            if not self.cache_object.cache_model:
                digital_twin_model = self.cache_object.load_cache(self.cache_model_path, self.cache_model_name)
                
                if not digital_twin_model:
                    module = importlib.import_module(self.cache_model_name)
                    digital_twin_model = getattr(module, self.cache_object_name)(self.model_path, self.model_parameters, self.dt_path)
                    with open(self.cache_model_path, 'wb') as f:
                        pickle.dump(digital_twin_model, f)
                        
                self.cache_object.cache_model =  digital_twin_model
                
            else:
                if self.cache_object.model_name == self.cache_object:
                    digital_twin_model = self.cache_object.cache_model
                    
                else:
                    digital_twin_model = self.cache_object.load_cache(self.cache_model_path, self.cache_model_name)
                    self.cache_object.cache_model =  digital_twin_model
                    
            copy_digital_twin_model = copy.deepcopy(digital_twin_model)
             
            if digital_twin_model.update_input(input_value):
                digital_twin_model.solve()
                if self.store_update():
                    self.cache_object.update_store(copy_digital_twin_model)
                return digital_twin_model.export_output()
            
        return None
