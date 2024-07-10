import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator import Orchestrator
from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin

class TestOrchestrator(unittest.TestCase):

    def setUp(self):
        self.path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json"
        self.model_parameters = {
            "model_path": "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh",
            "output_parameters":{
                "output_path": "./input/data",
                "output_format": ".h5"},
            "generation_models_list": [{
                "generator_path": "displacement_generator_fenicsxconcrete",
                "sensors_path": "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/20230215092338.json",
                "digital_twin_parameters_path" : "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json",
                "model_parameters": {
                    "model_name": "displacements",
                    "df_output_path":"../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv",
                    "meta_output_path":"../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json",
                    "MKP_meta_output_path":"../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json",
                    "MKP_translated_output_path":"../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json",
                    "virtual_sensor_added_output_path":"../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json",
                    "cache_path": "",
                    "paraview_output": True,
                    "paraview_output_path": "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview",
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
            }
            ]
        }     
        
        self.digital_twin = MagicMock()
        self.mock_parameters = self.model_parameters
    
    def test_initialization(self):
        orchestrator = Orchestrator(self.path)
        self.assertEqual(orchestrator.orchestrator_parameters, self.model_parameters)
        
    def test_predict_dt(self):
        orchestrator = Orchestrator(self.path)
        self.digital_twin.predict.return_value = 'test_prediction'
        result = orchestrator.predict_dt(self.digital_twin, 100)
        self.assertEqual(result, 'test_prediction')

    def test_predict_last_week(self):
        orchestrator = Orchestrator(self.path)
        self.digital_twin.predict.side_effect = ['prediction1', 'prediction2', None, 'prediction3']
        inputs = [100, 200, 300, 400]
        result = orchestrator.predict_last_week(self.digital_twin, inputs)
        self.assertEqual(result, ['prediction1', 'prediction2', 'prediction3'])

    def test_compare(self):
        orchestrator = Orchestrator(self.path)
        orchestrator.compare(200, 100)
        self.assertTrue(orchestrator.updated)
        orchestrator.compare(150, 100)
        self.assertFalse(orchestrator.updated)
        
    def test_run(self):
        orchestrator = Orchestrator(self.path)
        orchestrator.orchestrator_parameters = self.mock_parameters
        with unittest.mock.patch('nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin.DigitalTwin') as MockDigitalTwin:
            MockDigitalTwin.return_value = self.digital_twin

            # Call the run method
            orchestrator.run()

            # Assertions
            self.assertTrue(self.digital_twin.predict.called)
            # Add more specific assertions based on expected behavior
        


if __name__ == "__main__":
    unittest.main()
