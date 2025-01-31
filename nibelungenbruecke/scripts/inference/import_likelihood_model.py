import importlib

def import_likelihood_model(parameters):
    # Import the module from the filepath
    try:
        module = importlib.import_module("probeye.definition."+parameters.pop("module"))
    except ModuleNotFoundError:
        module = importlib.import_module("probeye.definition.likelihood_model")
    except KeyError:
        module = importlib.import_module("probeye.definition.likelihood_model")

    # Create an instance of the derived class with the given parameters
    model = getattr(module, parameters["name"])
    return model(**parameters["parameters"])