import sys
import importlib.util
from pathlib import Path

class Unpickler:
    def unpickle(self, path, name):
        module_path = self._model_addresses(name)
        
        # Load the module from the given path
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        
        module_directory = str(Path(module_path).parent)
        if module_directory not in sys.path:
            sys.path.append(module_directory)

        # Unpickle the object
        with open(path, 'rb') as file:
            obj = pickle.load(file)
        
        return obj
    
    @staticmethod 
    def _model_addresses(name):
        # Define how to resolve the module name to its path
        # For example, map module names to their paths
        module_paths = {
            'digital_twin_module': "../../../NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/displacement_model.py",
            'some_model': 'DisplacementModel.py'
        }
        return module_paths.get(name)