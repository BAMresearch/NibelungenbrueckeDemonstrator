import unittest
from unittest.mock import patch, mock_open, MagicMock
import pickle
import os
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator_cache import ObjectCache
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel


class TestObjectCache(unittest.TestCase):

    def setUp(self):
        self.cache_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/Displacement_1.pkl"
        self.model_name = "Displacement_1"
        self.test_model = DisplacementModel
        self.object_cache = ObjectCache()
        
    def test_load_cache_success(self):
        model = self.object_cache.load_cache(self.cache_path, self.model_name)
        self.assertIsInstance(model, self.test_model)
        self.assertEqual(self.object_cache.cache_model, self.test_model)
        self.assertEqual(self.object_cache.cache_path, self.cache_path)
        self.assertEqual(self.object_cache.model_name, self.model_name)

    def test_load_cache_file_not_found(self):
        self.object_cache.cache_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/wrong_path.pkl"
        model = self.object_cache.load_cache(self.cache_path, self.model_name)
        self.assertIsNone(model)

    def test_load_cache_unpickling_error(self):
        self.object_cache.cache_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/not_pickle"
        model = self.object_cache.load_cache(self.cache_path, self.model_name)
        self.assertIsNone(model)

    @patch('builtins.open', side_effect=Exception("Some error"))
    def test_load_cache_generic_error(self, mock_file):
        model = self.object_cache.load_cache(self.cache_path, self.model_name)
        self.assertIsNone(model)

    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump')
    def test_update_store_success(self, mock_pickle_dump, mock_file):
        self.object_cache.cache_path = self.cache_path
        self.object_cache.model_name = self.model_name
        self.object_cache.update_store(self.test_model)
        mock_pickle_dump.assert_called_once_with(self.test_model, mock_file())
        self.assertEqual(self.object_cache.cache_model, self.test_model)

    def test_update_store_path_not_set(self):
        self.object_cache.update_store(self.test_model)
        self.assertIsNone(self.object_cache.cache_model)

if __name__ == "__main__":
    unittest.main()
