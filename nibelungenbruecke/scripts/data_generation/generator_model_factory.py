import importlib

from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel

def generator_model_factory(model_path, filepath, sensor_positions, model_parameters, output_parameters=None):
    # Import the module from the filepath
    module = importlib.import_module("nibelungenbruecke.scripts.data_generation."+filepath)
    
    # Find the derived class of GeneratorModel in the imported module
    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, GeneratorModel) and obj != GeneratorModel:
            model_class = obj
            break
    else:
        raise ValueError(f"No derived class of GeneratorModel found in {filepath}")
    
    # Create an instance of the derived class with the given parameters
    return model_class(model_path, sensor_positions, model_parameters,output_parameters)