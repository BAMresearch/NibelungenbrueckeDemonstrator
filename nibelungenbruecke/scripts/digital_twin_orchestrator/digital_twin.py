from displacement_model import DisplacementModel


class  DigitalTwin:
    def __init__(self, model_path, model_parameters):
        self.model = {}

    def set_model(self):
        for param_models in model_list:
            self.model["{param_models['name']}"] = param_models["type"]
        
    def predict(self, input_value):
        if self.DisplacementModel.update_input(input_value):
            self.DisplacementModel.solve()
            return self.DisplacementModel.export_output()
        else:
            return None