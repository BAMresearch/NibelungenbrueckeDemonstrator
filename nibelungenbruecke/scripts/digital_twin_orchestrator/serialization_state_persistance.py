import importlib
import pickle

class DigitalTwinCache:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def get_model(self, model_name, object_name):
        key = (model_name, object_name)
        return self.cache.get(key)

    def add_model(self, model_name, object_name, model):
        key = (model_name, object_name)
        self.cache[key] = model
        self.save_cache()

