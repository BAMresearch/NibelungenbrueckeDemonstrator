from model import Model

class  DigitalTwin:
    def __init__(self, model_path, model_parameters):
        self.model = Model(model_path, model_parameters)
        
    def predict(self, input_value):
        if self.model.update_input(input_value):
            self.model.solve()
            return self.model.export_output()
        else:
            return None