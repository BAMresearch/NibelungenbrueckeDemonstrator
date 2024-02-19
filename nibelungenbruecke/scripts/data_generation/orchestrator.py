
class Model:
    def __init__(self):
        self.sensor_in = 0.0
        self.sensor_out = 0.0
        self.parameter = 2.0
    
    def update_input(self, input_value):
        if isinstance(input_value, (int, float)):
            self.sensor_in = input_value
            return True
        else:
            return False
    
    def solve(self):
        self.sensor_out = self.parameter * self.sensor_in
        return True
    
    def export_output(self):
        return self.sensor_out


class DigitalTwin:
    def __init__(self):
        self.model = Model()
    
    def predict(self, input_value):
        if self.model.update_input(input_value):
            if self.model.solve():
                return self.model.export_output()
        return None


class Orchestrator:
    def __init__(self):
        self.updated = False
    
    def predict_dt(self, digital_twin, input_value):
        return digital_twin.predict(input_value)
    
    def predict_last_week(self, digital_twin, inputs):
        outputs = []
        for input_value in inputs:
            output = digital_twin.predict(input_value)
            if output is not None:
                outputs.append(output)
        return outputs
    
    def compare(self, input_value, output_value):
        if output_value == 2 * input_value:
            self.updated = True


# Initialize Orchestrator and DigitalTwin
orchestrator = Orchestrator()
digital_twin = DigitalTwin()

# Feed an array of 7 random floats
import random
inputs = [random.uniform(1, 10) for _ in range(7)]

# Get predictions from DigitalTwin
predictions = orchestrator.predict_last_week(digital_twin, inputs)

# Check if predictions are correct and update Orchestrator state
for input_value, output_value in zip(inputs, predictions):
    orchestrator.compare(input_value, output_value)

# Check Orchestrator state
print("Orchestrator updated:", orchestrator.updated)
