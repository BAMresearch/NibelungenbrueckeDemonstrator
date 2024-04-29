#from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
from digital_twin import DigitalTwin

class Orchestrator:
    def __init__(self):
        self.updated = False
        
    def predict_dt(self, digital_twin, input_value):
        return digital_twin.predict(input_value)
    
    def predict_last_week(self, digital_twin, inputs):
        predictions = []
        for input_value in inputs:
            prediction = digital_twin.predict(input_value)
            if prediction is not None:
                predictions.append(prediction)
        return predictions

    def compare(self, output, input_value):
        self.updated = (output == 2 * input_value)

    def run(self, model_path, model_parameters, path, model_to_run, input_value=2.7*10**6):
        digital_twin = DigitalTwin(model_path, model_parameters, path, model_to_run)  # Assuming these parameters are available
        prediction = self.predict_dt(digital_twin, input_value)
        print("Prediction:", prediction)


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

    orch = Orchestrator()
    orch.run(model_path, model_parameters, dt_path, model_to_run= "Displacement_1")
