import unittest
from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator_cache import ObjectCache
import importlib
from unittest.mock import patch, mock_open, MagicMock
from unittest.mock import Mock
import json
import pickle

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
            'digital_twin_module': "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/displacement_model.py",
            'some_model': 'DisplacementModel.py'
        }
        return module_paths.get(name)
#%%
# =============================================================================
# if __name__ == "__main__":
#     UP = Unpickler()
#     
#     path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/Displacement_2.pkl"
#     name = 'digital_twin_module'
#     
#     UP.unpickle(path, name)
#     print(UP.unpickle(path, name))
#     
# =============================================================================
#%%

class TestDigitalTwin(unittest.TestCase):

    def setUp(self):
        
        self.model_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh"
        self.model_parameters =  {
                    "model_name": "displacements",
                    "df_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv",
                    "meta_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json",
                    "MKP_meta_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json",
                    "MKP_translated_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json",
                    "virtual_sensor_added_output_path":"/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json",
                    "paraview_output": True,
                    "paraview_output_path": "./output/paraview",
                    "material_parameters":{},
                    "tension_z": 0.0,
                    "boundary_conditions": {
                        "bc1":{
                        "model":"clamped_boundary",
                        "side_coord": 0.0,
                        "coord": 2
                    },
                        "bc2":{
                        "model":"clamped_boundary",
                        "side_coord": 95.185,
                        "coord": 2
                    }}
                }
        self.dt_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'
        self.model_to_run = "Displacement_1"
        
        self.cache_model_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/Displacement_2.pkl"

        self.digital_twin = DigitalTwin(
            model_path=self.model_path,
            model_parameters=self.model_parameters,
            dt_path=self.dt_path,
            model_to_run=self.model_to_run
        )
        
    def test_initialization(self):
        dt = self.digital_twin
        self.assertEqual(dt.model_path, self.model_path)
        self.assertEqual(dt.model_parameters, self.model_parameters)
        self.assertEqual(dt.dt_path, self.dt_path)
        self.assertEqual(dt.model_to_run, self.model_to_run)
        self.assertIsInstance(dt.cache_object, ObjectCache)

    def test_load_models(self):
        dt = self.digital_twin
        
        with open(self.dt_path, 'r') as json_file:
            models = json.load(json_file)
        
        dt.load_models()
        
        self.assertEqual(dt.models, models)
    
    def test_set_model(self):
        dt = self.digital_twin
        dt.set_model()
                
        with open(self.dt_path, 'rb') as f:
            set_model = json.load(f)
        
        self.assertEqual(dt.cache_model_name, set_model[0]["type"])
        self.assertEqual(dt.cache_object_name, set_model[0]["class"])
        self.assertEqual(dt.cache_model_path, set_model[0]["path"])
        
    
    #TODO: Need to make this work
    @patch('digital_twin.DisplacementModel.update_input', return_value=False)
    def test_predict(self, mock_update_input):
        dt = self.digital_twin
        dt.cache_object = ObjectCache()
        dt.set_model()
                
        UP = Unpickler()
        path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/" + dt.cache_model_path
        name = 'digital_twin_module'
        expected_model = UP.unpickle(path, name)
        
        mock_update_input.return_value = False
        # Call predict method
        result = dt.predict(3*10**9)
        
        # Check if the model was correctly cached
        self.assertEqual(dt.cache_object.cache_model, expected_model)

if __name__ == "__main__":
    unittest.main()
