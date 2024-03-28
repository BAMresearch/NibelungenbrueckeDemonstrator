class Model:
    def __init__(self):
        self.sensor_in = 0.0
        self.sensor_out = 0.0
        self.parameter = 2.0

    def update_input(self, sensor_input):
        if isinstance(sensor_input, (int, float)):
            self.sensor_in = sensor_input
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
            self.model.solve()
            return self.model.export_output()
        else:
            return None


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


# Example usage
if __name__ == "__main__":
    import random

    orchestrator = Orchestrator()
    digital_twin = DigitalTwin()

    inputs = [random.uniform(0, 10) for _ in range(7)]
    outputs = orchestrator.predict_last_week(digital_twin, inputs)

    print("Inputs:", inputs)
    print("Outputs:", outputs)

    for i in range(len(inputs)):
        orchestrator.compare(outputs[i], inputs[i])

    print("Orchestrator state updated:", orchestrator.updated)
