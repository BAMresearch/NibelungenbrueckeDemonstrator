import os
import json
import pickle
import importlib

from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator_cache import ObjectCache


class DigitalTwin:
    """
    Manages digital twin models, handling model initialization, predictions, caching, 
    and parameter updates.
    
    Attributes:
        model_to_run (str): Specifies which predefined model to execute.
        orchestrator_parameters (dict): Stores parameters extracted from the JSON model file.
        digital_twin_models (dict): Stores initialized digital twin models.
        cache_object (ObjectCache): Manages caching of models and parameters.
        
    """
    
    def __init__(self, model_parameters_path: dict, model_to_run = "Displacement_1"): 
        """
       Initializes the DigitalTwin instance.
       
       Args:
           model_parameters_path (str): Path to the JSON file containing model parameters.
           model_to_run (str): Specifies which predefined model to execute. Defaults to "Displacement_1".
           
       """
        self.model_to_run = model_to_run
        self.orchestrator_parameters = self._extract_model_parameters(model_parameters_path)
        self._load_models()
        self.cache_object = ObjectCache()
        self.digital_twin_models = {}
    
    def _extract_model_parameters(self, path):
        """
        Loads parameters from a JSON file.
        
        Args:
            path (str): Path to the JSON file.
        
        Returns:
            dict: Extracted model parameters.
        """
        
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: The file {path} was not found!")
        except json.JSONDecodeError:
            raise ValueError("Error: Failed to parse JSON file!")
            
    def _load_models(self):
        """
        Loads the predefined model parameters from the json file.
        
        """
        dt_params_path = self.orchestrator_parameters["generation_models_list"][0]["digital_twin_parameters_path"]      ##TODO: !!
        try:
            with open(dt_params_path, 'r') as json_file:
                self._models = json.load(json_file)
        except Exception as exc:
            try:
                dt_params_path = dt_params_path.strip("../")
                with open(dt_params_path, 'r') as json_file:
                    self._models = json.load(json_file)
            except:
                raise RuntimeError('Failed to open the path!') from exc
        
    def predict(self, model_to_run, api_key, orchestrator_simulation_parameters, UQ_flag):
        """
        Predicts the outcome based on the input value by setting up and running a model.
        
        Args:
            input_value (list|dict): Input data for prediction.
            model_to_run (str): The model to execute.
        

        """
        self.model_to_run = model_to_run
        
        if not self._set_model(orchestrator_simulation_parameters):
            #self.digital_twin_model = self._initialize_default_model()  ## TODO:
            #return 
            raise ValueError(f"There isn't any predefined model with name {self.model_to_run}. Please check the name or add the model to model parameters\n")

            
        if self.model_to_run not in self.digital_twin_models.keys() or UQ_flag:
            self._loaded_params = self._get_or_load_parameters()
            self.initial_model = self._initialize_default_model(api_key, orchestrator_simulation_parameters)
        else:
            self.initial_model = self.digital_twin_models[self.model_to_run]
            
        updated = False
        updated_params = {}
            
        if "TransientThermal" in self.model_to_run:
            updated = True
            updated_params["parameters"] = {}
        elif "Displacement" in self.model_to_run:
            input_value = self.initial_model.generate_random_parameters()
            updated, updated_params = self.initial_model.update_parameters(input_value, self.model_to_run)
            
        if updated:
            self._update_cached_model(self._loaded_params, updated_params)
            self._run_model(api_key, orchestrator_simulation_parameters)
        else:
            print("Same model with the same parameters!!\n")
            return None
            
        return self.initial_model
    

    def _set_model(self, orchestrator_simulation_parameters):
        """
        Sets up the model based on predefined configurations.
    
        Returns:
            bool: True if the model is successfully set, otherwise raises an error.
    
        Raises:
            ValueError: If the specified model is not found in the JSON file.
        """
        for model_info in self._models:
            if model_info["name"] == orchestrator_simulation_parameters["model"]:
                # Always start from base type/class/path
                base_type = model_info["type"]
                base_class = model_info["class"]
                base_path = model_info["path"]
    
                rel_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/"
    
                if orchestrator_simulation_parameters.get("uncertainty_quantification", False):
                    # Append UQ-related suffixes only once
                    self.cache_model_name = base_type if base_type.endswith("_uq") else base_type + "_uq"
                    self.cache_object_name = base_class if base_class.endswith("UQ") else base_class + "UQ"
                    if not base_path.endswith("_UQ.json"):  # customize this if needed
                        parts = base_path.split(".", 1)
                        new_path = f"{parts[0]}_UQ.{parts[1]}"
                        self.cache_model_path = rel_path + new_path
                    else:
                        self.cache_model_path = rel_path + base_path
                else:
                    # In classic mode, keep names clean
                    self.cache_model_name = base_type.replace("_uq", "")
                    self.cache_object_name = base_class.replace("UQ", "")
                    self.cache_model_path = rel_path + base_path
    
                return True
    
        raise ValueError(f"'{self.model_to_run}' not found in the defined models.")

    
# =============================================================================
#     def _set_model(self, orchestrator_simulation_parameters):       ##TODO: 
#         """
#         Sets up the model based on predefined configurations.
#         
#         Returns:
#             bool: True if the model is successfully set, otherwise raises an error.
#         
#         Raises:
#             ValueError: If the specified model is not found in the JSON file.
#         """
# 
#         for model_info in self._models:
#             if model_info["name"] == orchestrator_simulation_parameters["model"]:
#                 self.cache_model_name = model_info["type"]
#                 self.cache_object_name = model_info["class"]
#                 rel_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/" ##TODO:
#                 self.cache_model_path = rel_path + model_info["path"]
#                 
#                 if orchestrator_simulation_parameters["uncertainty_quantification"]:
#                     self.cache_model_name = self.cache_model_name + "_uq"
#                     self.cache_object_name = model_info["class"] + "UQ"
#                     parts = model_info["path"].split(".", 1)
#                     new_path = f"{parts[0]}_UQ.{parts[1]}"
#                     self.cache_model_path = rel_path + new_path
#                     
#                 return True
#         raise ValueError(f"'{self.model_to_run}' not found in the defined models.")     ##TODO: Create a new model !!
# =============================================================================
    
    def _get_or_load_parameters(self):
        """
        Retrieves cached model parameters or loads default parameters if the cache is missing.
                
        Returns:
            dict: Model parameters.
        """
        if not self.cache_object.cache_model:
            parameters = self.cache_object.load_cache(self.cache_model_path, self.cache_model_name)
            if not parameters:
                with open(self._default_parameters_path(), 'r') as file:
                    parameters = json.load(file)
                self.cache_object.cache_model = parameters
        else:
            if self.cache_object.model_name != self.cache_object_name:      ##TODO
                parameters = self.cache_object.load_cache(self.cache_model_path, self.cache_model_name)
                if not parameters:
                    with open(self._default_parameters_path(), 'r') as file:
                        parameters = json.load(file)
                        
                self.cache_object.cache_model = parameters
            else:
                parameters = self.cache_object.cache_model
        
        return parameters
    
    def _initialize_default_model(self, api_key, orchestrator_simulation_parameters):
        """
        Initializes the digital twin model from the default parameters.
        
        Returns:
            object: An instance of the selected digital twin model.
        
        Raises:
            ValueError: If the selected model is not found.
        """
        
        model_name = orchestrator_simulation_parameters["model"]
        model_found = False
    
        for model in self._models:
            if model["name"] != model_name:
                continue
            
            model_found = True
    
            model_paths = self.cache_object.cache_model["model_path"][0]
            if "TransientThermal" in self.model_to_run:
                model_path = model_paths["transientthermal_model_path"]
            elif "Displacement" in self.model_to_run:
                model_path = model_paths["displacement_model_path"]
            else:
                raise ValueError(f"Unknown model type '{self.model_to_run}'. Check the default parameter JSON file.")
    
            # Load model parameters
            generation_model_parameters = self.cache_object.cache_model["generation_models_list"][0]
            model_parameters = generation_model_parameters["model_parameters"]
            dt_params_path = generation_model_parameters["digital_twin_parameters_path"]
    
            # Apply uncertainty quantification flag
            if orchestrator_simulation_parameters.get("uncertainty_quantification"):
                if "_uq" not in model["type"]:
                    model["type"] += "_uq"
                if "UQ" not in model["class"]:
                    model["class"] += "UQ"
                    
            else:
                model["type"] = model["type"].replace("_uq", "")
                model["class"] = model["class"].replace("UQ", "")
                
    
            # Set plot flag
            plot_pv = orchestrator_simulation_parameters.get("plot_pv", False)
            model_parameters["thermal_model_parameters"]["model_parameters"]["problem_parameters"]["plot_pv"] = plot_pv
    
            # Import and instantiate the model
            module = importlib.import_module(model["type"])
            model_class = getattr(module, model["class"])
            digital_twin_model = model_class(model_path, model_parameters, dt_params_path)

            # Generate the model
            digital_twin_model.GenerateModel()
                
        
            # Set plot flag in the instantiated problem
            digital_twin_model.problem.p["plot_pv"] = plot_pv
            digital_twin_model.model_parameters["API_request_start_time"] = orchestrator_simulation_parameters["start_time"]
            digital_twin_model.model_parameters["API_request_end_time"] = orchestrator_simulation_parameters["end_time"]
            
            # Store and return
            self.digital_twin_models[self.model_to_run] = digital_twin_model
            return digital_twin_model
    
        if not model_found:
            raise ValueError(f"Model '{model_name}' not found in available models.")
        

    
    def _update_cached_model(self, parameters, updated_params):
        """
        Updates the cached model with new parameters and stores the changes.
        
        """
        self.cache_object.cache_model["generation_models_list"][0]["model_parameters"]["material_parameters"] = updated_params["parameters"]
        self.cache_object.update_store(parameters)
        self.initial_model.model_parameters = self.cache_object.cache_model["generation_models_list"][0]["model_parameters"]
         
    def _run_model(self, api_key, orchestrator_simulation_parameters):
        """
        Extracts latest version of the model that saved last time.
        
        This provides flexibility to switch between different models, allowing for the assignment 
        of field data without having to recreate the models from scratch.
        
        """
        self.uploader()
        self.initial_model.fields_assignment(self.model_params)
        self.initial_model.solve(api_key, orchestrator_simulation_parameters["virtual_sensor_positions"])
        self.initial_model.fields_data_storer(self.model_to_run)

        return self.initial_model
    

        
    def uploader(self):
        """
        Loads model parameters from a serialized pickle file.
        
        Returns:
            dict or None: Loaded model parameters or None if the file is missing.
        """
        try:
            ##TODO: 
            rel_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/"
            with open(f"{rel_path}{self.model_to_run}_params.pkl", "rb") as f:
                self.model_params = pickle.load(f)                
                return self.model_params
        
        except FileNotFoundError:
            self.model_params = None
            print(f"Error: The file {self.model_to_run} was not found!")    #TODO: Use assertion instead!!
            return None
        
        except Exception as e:
            print(f"An unexpected error!: {e}")
    
    def _default_parameters_path(self):
        """
        Returns the default parameters file path.
        """
        default_parameters_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json"
        
        ##TODO: !!
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, default_parameters_path)
        json_path = os.path.normpath(json_path)
        
        return json_path
   
    def store_update(self):            
        measured_vs_path = self.model_parameters["virtual_sensor_added_output_path"]
        with open(measured_vs_path, 'r') as f:
            sensor_measurement = json.load(f)
            
        triggered = False    
        for i in sensor_measurement["virtual_sensors"].keys():
            if sensor_measurement["virtual_sensors"][i]["displacements"][-1] == sensor_measurement["virtual_sensors"][i]["displacements"][-2]:
                triggered = False
            else:
                triggered = True
                
        return triggered