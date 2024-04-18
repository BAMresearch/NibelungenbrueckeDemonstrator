from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin

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

    def run(self):
        
        dt = DigitalTwin()
        input_value = 10
        prediction = self.predict_digital_twin(dt, input_value)
        print("Prediction:", prediction)

#%%
if __name__ == "__main__":
    o = Orchestrator()
    dt = DigitalTwin()
    o.predict_dt(dt, input)