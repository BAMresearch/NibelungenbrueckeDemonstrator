import importlib

def import_likelihood_model(parameters):
    # Import the module from the filepath
    module = importlib.import_module("probeye.definition.likelihood_model")

    # Create an instance of the derived class with the given parameters
    model = getattr(module, parameters["name"])
    return model(**parameters["parameters"])