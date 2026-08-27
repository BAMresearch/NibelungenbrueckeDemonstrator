import os
import json
import pickle
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel

class ObjectCache:
    def __init__(self):
        self.cache_path = None
        self.model_name = None
        self.cache_model = None
    
    def load_cache(self, cache_path, model_name):
        self.cache_path = cache_path
        self.model_name = model_name
        
        try:
                
            with open(self.cache_path, 'rb') as f:
                             self.cache_model = json.load(f)
                             #print(f"Model '{self.model_name}' loaded successfully -> {self.cache_model}.")
                             return self.cache_model
        except FileNotFoundError:
                         print(f"\nWarning: The file '{self.cache_path}' was not found and will be created during the process.")
                         return None
            
        
    def update_store(self, model):
        if self.cache_path is None or self.model_name is None:
            print("Error: cache_path and model_name must be set before saving the model.")
            return

        try:
            with open(self.cache_path, 'w') as file:
                json.dump(model, file, indent=4)
                print(f"New model '{self.model_name}' saved successfully.")
                
            # Update the cache_model attribute
            self.cache_model = model
            
        except Exception as e:
            print(f"An error occurred while saving the model: {e}")

#%%
if __name__ == "__main__":
    path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/nibelungenbruecke/scripts/digital_twin_orchestrator/Displacement_1.pkl"
    
    model_name = "Displacement_1"
        
    Model = ObjectCache()
    Model.load_cache(path, model_name)