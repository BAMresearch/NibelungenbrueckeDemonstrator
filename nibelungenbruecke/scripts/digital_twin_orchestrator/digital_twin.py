from displacement_model import DisplacementModel
import json
import importlib

class  DigitalTwin:
    def __init__(self, model_path, model_parameters, path, model_to_run = "Displacement_1"):   #TODO: place path and model_to_run paramters into the JSON!!
        self.model_path = model_path
        self.model_parameters = model_parameters
        self.path = path
        self.model_to_run = model_to_run
        self.load_models()
        
    def load_models(self):
        with open(self.path, 'r') as json_file:
            self.models = json.load(json_file)
        
    def set_model(self):
        for model_info in self.models:
            if model_info["name"] == self.model_to_run:
                self.model_name = model_info["type"]
                self.object_name = model_info["class"]
                return True
        return False
    
    def predict(self, input_value):
        if self.set_model():
            module = importlib.import_module(self.model_name)
            digital_twin_model = getattr(module, self.object_name)(self.model_path, self.model_parameters, self.path)
            if digital_twin_model.update_input(input_value):
                digital_twin_model.solve()
                return digital_twin_model.export_output()
            
        return None
  
#%%

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


    DTM = DigitalTwin(model_path, model_parameters, dt_path)
    DTM.set_model()
    DTM.predict(3*10**9)
    DTM.GenerateData()
    
    vs_file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
    DTM.solve(vs_file_path)
    
    DTM.export_output()

