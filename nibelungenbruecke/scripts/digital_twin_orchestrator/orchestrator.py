from digital_twin import DigitalTwin


"""
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


### -- ##
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
"""