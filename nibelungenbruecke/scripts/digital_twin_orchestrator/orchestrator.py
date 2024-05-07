#from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
from digital_twin import DigitalTwin
import json

class Orchestrator:
    def __init__(self, model_parameters_path: str):
        self.updated = False
        with open(model_parameters_path, 'r') as file:
            self.model_parameters = json.load(file)
        
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

    def run(self):
        input_value=2.7*10**6   #TODO: should also be a part of the chosen model.!!
        model_path = self.model_parameters["model_path"]
        model_parameters = self.model_parameters["generation_models_list"][0]["model_parameters"]
        dt_path = self.model_parameters["generation_models_list"][0]["digital_twin_parameters_path"]
        digital_twin = DigitalTwin(model_path, model_parameters, dt_path, model_to_run = "Displacement_1")
        prediction = self.predict_dt(digital_twin, input_value)
        print("Prediction:", prediction) #TODO: Remove this!!

#%%
if __name__ == "__main__":
    path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json"
    #with open(path, 'r') as file:
    #    a = json.load(file)
    
    orchestrator = Orchestrator(path)
    orchestrator.run()
    
    #import os
    #print(os.getcwd())
    #print(os.path.dirname(os.path.abspath(__file__)))

#%%

"""
import os

current_dir = os.getcwd()
print("Current Directory:",current_dir)

file_path = 'input/settings/generate_data_parameters.json'
full_path = os.path.join(current_dir, file_path)
print("Full Path:", full_path)

/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/input/settings/generate_data_parameters.json

if os.path.exists(full_path):
    print("File exists!")
else:
    print("File does not exist!")
"""