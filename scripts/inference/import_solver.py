import importlib

def import_solver(problem, parameters):
    # Import the module from the filepath
    module = importlib.import_module("probeye.inference."+parameters.pop("module")+".solver")

    # Create an instance of the derived class with the given parameters
    model = getattr(module, parameters.pop("name"))
    return model(problem, **parameters)