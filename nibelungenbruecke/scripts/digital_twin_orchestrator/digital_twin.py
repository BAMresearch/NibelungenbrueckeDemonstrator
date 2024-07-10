import sys
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel
import json
import importlib
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
                self.cache_model_path = model_info["path"]
                return True
        return False
            
    def predict(self, input_value):      
        if self.set_model():
            
            if not self.cache_object.cache_model:
                digital_twin_model = self.cache_object.load_cache(self.cache_model_path, self.cache_model_name)
                
                if not digital_twin_model:
                    module = importlib.import_module(self.cache_model_name)
                    digital_twin_model = getattr(module, self.cache_object_name)(self.model_path, self.model_parameters, self.dt_path)
                    sys.path.append(module.__path__)
                    with open(self.cache_model_path, 'wb') as f:
                        pickle.dump(digital_twin_model, f)
                        
                self.cache_object.cache_model =  digital_twin_model
                
            else:
                if self.cache_object.model_name == self.cache_object:
                    digital_twin_model = self.cache_object.cache_model
                    
                else:
                    digital_twin_model = self.cache_object.load_cache(self.cache_model_path, self.cache_model_name)
                    self.cache_object.cache_model =  digital_twin_model 
                    
            
            self.cache_object.update_store(digital_twin_model)
                    
            if digital_twin_model.update_input(input_value):
                digital_twin_model.solve()
                return digital_twin_model.export_output()
            
        return None
