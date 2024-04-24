from displacement_model import DisplacementModel
import json
import importlib

class  DigitalTwin:
    def __init__(self, model_path, model_parameters, path, model_to_run):
        self.model = []
        self.path = path
        self.model_to_run = model_to_run

    def set_model(self, json_file):
        with open(self.path, 'r') as json_file:
            self.parameters = json.load(json_file)
        
        for i in range(len(self.parameters)):
            params = {}
            for task, task_model in self.parameters[i].items():
                if task != "parameters":
                    params[task] = task_model
                print(params)
            self.model.append(params)
        
        for i in self.model:
            if self.model_to_run == i["name"]:
                self.model_name = i["type"]
                
        return self.model_name
        
    def predict(self, input_value):
        module = importlib.import_module("nibelungenbruecke.scripts.digital_twin_orchestrator." + self.model_name)
        if module.update_input(input_value):
            module.solve()
            return module.export_output()
        else:
            return None