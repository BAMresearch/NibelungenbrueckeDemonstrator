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
                    #self.cache.add_object(self.model_name, self.object_name, digital_twin_model)
                    #export_output = self.model_to_run + ".pkl"
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
    
#%%
import pickle

if __name__ == "__main__":
    model_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh"
    sensor_positions_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/20230215092338.json"
    model_parameters =  {
                "model_name": "displacements",
                "df_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv",
                "meta_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json",
                "MKP_meta_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json",
                "MKP_translated_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json",
                "virtual_sensor_added_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json",
                "paraview_output": True,
                "paraview_output_path": "./output/paraview",
                "material_parameters":{},
                "tension_z": 0.0,
                "boundary_conditions": {
                    "bc1":{
                    "model":"clamped_boundary",
                    "side_coord": 0.0,
                    "coord": 2
                },
                    "bc2":{
                    "model":"clamped_boundary",
                    "side_coord": 95.185,
                    "coord": 2
                }}
            }
    output_parameters = {
            "output_path": "./input/data",
            "output_format": ".h5"}

    dt_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'

    DTM = DigitalTwin(model_path, model_parameters, dt_path, model_to_run="Displacement_1")

    with open("pickle_data.pkl", "wb") as f:
        pickle.dump(DTM, f)
        
    with open("pickle_data.pkl", "rb") as f:
        loaded_data = pickle.load(f)
        
    loaded_data.set_model()
    loaded_data.predict(3*10**9)
    
    vs_file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
    DTM.solve(vs_file_path)
    
    
    
    
    DTM.export_output()

