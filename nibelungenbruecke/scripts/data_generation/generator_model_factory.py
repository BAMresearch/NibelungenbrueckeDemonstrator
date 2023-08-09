import importlib

from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel

def generator_model_factory(model_path, filepath, sensor_positions, model_parameters, output_parameters=None):
    # Import the module from the filepath
    module = importlib.import_module("nibelungenbruecke.scripts.data_generation."+filepath)
    
    # Find all subclasses of GeneratorModel in the imported module
    subclasses = []
    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, GeneratorModel) and obj != GeneratorModel:
            subclasses.append(obj)
    
    # Eliminate those that are superclasses of others
    for subclass in list(subclasses):  # iterate over a copy so we can modify the original list
        for potential_subclass in subclasses:
            if issubclass(potential_subclass, subclass) and potential_subclass != subclass:
                subclasses.remove(subclass)
                break
    
    if not subclasses:
        raise ValueError(f"No derived class of GeneratorModel found in {filepath}")
    
    if len(subclasses) > 1:
        raise ValueError(f"Multiple derived classes of GeneratorModel found in {filepath}")
    
    # Create an instance of the derived class with the given parameters
    return subclasses[0](model_path, sensor_positions, model_parameters,output_parameters)