import importlib

from probeye.definition.forward_model import ForwardModelBase

def forward_model_factory(filepath, model_parameters, model_path):
    # Import the module from the filepath
    module = importlib.import_module("nibelungenbruecke.scripts.inference."+filepath)
    
    # Find the derived class of ForwardModelBase in the imported module
    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, ForwardModelBase) and obj != ForwardModelBase:
            model_class = obj
            break
    else:
        raise ValueError(f"No derived class of ForwardModelBase found in {filepath}")
    
    # Create an instance of the derived class with the given parameters
    model = model_class(model_parameters["name"], forward_model_parameters = model_parameters)
    
    return model