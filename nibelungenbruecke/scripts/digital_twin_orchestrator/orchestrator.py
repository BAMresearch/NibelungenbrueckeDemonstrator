from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
import json

class Orchestrator:
    def __init__(self, model_parameters_path: str):
        self.updated = False
        with open(model_parameters_path, 'r') as file:
            self.orchestrator_parameters = json.load(file)
        
    def predict_dt(self, digital_twin, input_value):
        return digital_twin.predict(input_value)
    
    def predict_last_week(self, digital_twin, inputs):
        predictions = []
        for input_value in inputs:
            prediction = digital_twin.predict(input_value)
            if prediction is not None:
                predictions.append(prediction)
        return predictions

    def compare(self, output, input_value): #TODO
        self.updated = (output == 2 * input_value)

    def run(self):
        input_value=round(2.7*10**11, 1)   #TODO: !!
        model_path = self.orchestrator_parameters["model_path"]
        model_parameters = self.orchestrator_parameters["generation_models_list"][0]["model_parameters"]
        dt_path = self.orchestrator_parameters["generation_models_list"][0]["digital_twin_parameters_path"]
        digital_twin = DigitalTwin(model_path, model_parameters, dt_path, model_to_run = "Displacement_2")
        prediction = self.predict_dt(digital_twin, input_value)
        #prediction = self.predict_last_week(digital_twin, input_value)
        print("Prediction:", prediction) #TODO