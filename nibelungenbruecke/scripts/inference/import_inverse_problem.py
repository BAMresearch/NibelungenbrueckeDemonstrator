import importlib

def import_inverse_problem(parameters):
    # Import the module from the filepath
    try:
        module = importlib.import_module("probeye.definition."+parameters.pop("module"))
        model = getattr(module, parameters.pop("model_name")) 
    except KeyError: # This should avoir breaking the code when the module is not specified
        module = importlib.import_module("probeye.definition.inverse_problem")
        model = getattr(module, "InverseProblem") 

    # Create an instance of the derived class with the given parameters
    return model(**parameters)