
import importlib
import time
import pickle
import json
import matplotlib.pyplot as plt
import numpy as np
import random
from datetime import datetime

import dolfinx as df
from fenicsxconcrete.util import ureg
from nibelungenbruecke.scripts.data_generation.linear_elasticity_nibelungenbruecke_demonstrator import LinearElasticityNibelungenbrueckeDemonstrator

from nibelungenbruecke.scripts.utilities.loaders import load_sensors
from nibelungenbruecke.scripts.utilities.offloaders import offload_sensors
from nibelungenbruecke.scripts.digital_twin_orchestrator.base_model import BaseModel
from nibelungenbruecke.scripts.data_generation.nibelungen_experiment import NibelungenExperiment
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request, MetadataSaver, Translator

class DisplacementModel(BaseModel):
    """
    A class representing a displacement model for NB simulations.
    
    """
    
    def __init__(self, model_path: str, model_parameters: dict, dt_path: str):
        """
        Initializes the DisplacementModel with the given paths and parameters.
        
        Args:
            model_path (str): Path to the model directory.
            model_parameters (dict): Dictionary containing material properties 
            and model-specific parameters.
            dt_path (str): Path to the digital twin parameter file (JSON format).
        """
        
        super().__init__(model_path, model_parameters)
        
        self.model_parameters = model_parameters
        self.material_parameters = self.model_parameters["material_parameters"]
        self.default_p = self._get_default_parameters()
        self.dt_path = dt_path
        self.vs_path = self.model_parameters["virtual_sensor_added_output_path"] ##TODO: !!
        #self.experiment = NibelungenExperiment(self.model_path, self.model_parameters)
        
    def LoadGeometry(self):
        """
        Loads the geometry of the model for simulation.
        
        """
        pass
    
    def GenerateModel(self):
        """
        Generates the model by setting up the attributes experiment and problem with their parameters.
        
        This includes setting up material parameters and solving related data 
        using the `LinearElasticityNibelungenbrueckeDemonstrator` and 'NibelungenExperiment' .
        """
        
        self.experiment = NibelungenExperiment(self.model_path, self.model_parameters)
        #self.default_p.update(self.experiment.parameters)
        self.problem = LinearElasticityNibelungenbrueckeDemonstrator(
            [self.GenerateData, self.PostAPIData, self.ParaviewProcess], self.experiment, self.experiment.parameters,
            pv_name=self.model_parameters["paraview_displacement_output_name"],pv_path=self.model_parameters["paraview_output_path"])
        
    def GenerateData(self, api_key):
        """
        Requests data from an API, transforms it into metadata, 
        and saves it for use with virtual sensors.

        """
        
        self.api_request = API_Request(api_key, start_time = self.model_parameters["API_request_start_time"], 
                                       end_time=self.model_parameters["API_request_end_time"], time_step=self.model_parameters["API_request_time_step"])
        self.api_dataFrame = self.api_request.fetch_data()

        metadata_saver = MetadataSaver(self.model_parameters, self.api_dataFrame)
        metadata_saver.saving_metadata()

        self.translator = Translator(self.model_parameters)
        self.translator.translator_to_sensor(self.experiment.mesh)
        
        self.problem.import_sensors_from_metadata(
            self.model_parameters["MKP_meta_output_path"])
        
    def SolveMethod(self):
        """
       Solves the model using a dynamic solver.
       
       This method is called during the solution process of the displacement model.
       """
        self.problem.dynamic_solve()        ##TODO: change the name!
        
    def PostAPIData(self):
        """
        Saving data of virtual sensor' after the model solve
        """
        
        self.translator.save_to_MKP(self.api_dataFrame)
        self.translator.save_virtual_sensor(self.problem)        
        
    def ParaviewFirstRun(self):
        """
        Handles the first run of Paraview data output.
        
        This method is useful for initializing the Paraview output for the 
        first time, setting up the model visualization,
        and preparing the mesh for further data writing in later iterations.
        """
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]+ "/" +
                                self.model_parameters["paraview_displacement_output_name"] +".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                #xdmf.write_function(self.problem.fields.displacement, self.problem.time)     
                
    def ParaviewProcess(self):
        """
        Processes the Paraview data during each timestep.
        It writes the displacement fields to the Paraview XDMF file.
        """
        
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, 
                                self.model_parameters["paraview_output_path"]+ "/" +
                                self.model_parameters["paraview_displacement_output_name"]+".xdmf", "a") as xdmf:
                # xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement, 
                                    self.problem.time)
                
    @staticmethod
    def _get_default_parameters():
        """
        Get default material parameters.

        Returns:
            dict: Default material parameters.
        """
        default_parameters = {
            "rho":7750 * ureg("kg/m^3"),
            "E":210e9 * ureg("N/m^2"),
            "nu":0.28 * ureg("")
        }
        return default_parameters

    def update_parameters(self, updates, target_name=None):
        """
        Updates the specified parameters in the digital twin parameter file 
        (JSON format).
        
        Args:
            updates (dict): A dictionary containing parameters to be updated 
            (key: value).
            target_name (str): The name of the model whose parameters need to 
            be updated (optional).
        

        """
        try:
            with open(self.dt_path, 'r') as f:
                dt_params = json.load(f)
    
            updated = False
            model_type_params = None
            
            # Update parameters in matching entries
            for entry in dt_params:
                if entry["name"] == target_name:
                    for key, value in updates.items():
                        if key in entry["parameters"]:
                            if entry["parameters"][key] != value:
                                entry["parameters"][key] = value
                                self.problem.p[key] = value  ##TODO: problem.p update!!
                                model_type_params = entry
                                updated = True
   
            # Save the updated JSON back to the file
            if updated:
                with open(self.dt_path, 'w') as file:
                    json.dump(dt_params, file, indent=4)
                return True, model_type_params
            else:
                return False, None
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def solve(self, api_key):
        """
        Reloading, model generating and solving model.
        
        With use of callback() methods, ceratin methods are called in each step 
        of moving load case.
        
        TODO:
            The re-loading of the model can be avoidede by recalculating and 
            modifying the values in the constant fields of the Lamé constants
            

        """
        self.LoadGeometry()
        self.GenerateModel()
        self.GenerateData(api_key)
        self.ParaviewFirstRun()
        self.SolveMethod()
        self.sensor_out = self.api_dataFrame['E_plus_080DU_HSN-u-_Avg1'].iloc[-1] # *1000 #Convertion from meter to milimeter
 
        vs_file_path = self.model_parameters["virtual_sensor_added_output_path"]
        with open(vs_file_path, 'r') as file:
            self.vs_data = json.load(file)        
        
        self.vs_sensor_out = self.vs_data['virtual_sensors']['E_plus_080DU_HSN-u-_Avg1']['displacements'][-1][0]
        
        print(f"Real sensor measurement: {self.sensor_out}")
        print(f"Virtual sensor measurement: {self.vs_sensor_out}")
        
        self.plot_displacement()
        

    def generate_random_parameters(self):
        """
        Generates 'rho' and 'E' values.
        """
        params: dict={}
        random_value_rho = random.randint(90 // 5, 160 // 5) * 100
        random_value_E = random.randint(100 // 5, 225 // 5) * 10**10
        params['rho'] = random_value_rho
        params['E'] = random_value_E

        return params 
    
    def plot_displacement(self):
        with open(self.vs_path, 'r') as file:
            data = json.load(file)
    
        timestamps = data.get("df", {}).get("index", [])
        columns = data.get("df", {}).get("columns", [])
        real_values = data.get("df", {}).get("data", [])
        virtual_values = data.get("virtual_sensors", {})
    
        if not timestamps or not real_values or not virtual_values:
            raise ValueError("JSON file does not contain valid time-series data.")
    
        # Convert timestamps to datetime objects for better plotting
        timestamps = [datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps]
    
        plt.figure(figsize=(12, 6))
    
        for i, column in enumerate(columns):
            column_values = [row[i] for row in real_values]
            
            # Plot real values
            plt.plot(timestamps, column_values, label=f"{column} (real)", linestyle='-')
    
            if column in virtual_values and "displacements" in virtual_values[column]:
                virtual_column_values = [row[1] for row in virtual_values[column]["displacements"]]
                
                interp_virtual_values = np.interp(
                    np.linspace(0, len(column_values) - 1, len(column_values)),
                    np.linspace(0, len(column_values) - 1, len(virtual_column_values)),
                    virtual_column_values
                )
                
                plt.plot(timestamps, interp_virtual_values, linestyle='--', label=f"{column} (virtual)")
    
            # Optionally plot the real sensor values as well
            # plt.plot(timestamps, column_values, label=f"{column} (real)")
    
        plt.title("Displacement Over Time")
        plt.xlabel("Time")
        plt.ylabel("Displacement")
        plt.legend()
        plt.tight_layout()
        plt.grid(True)
        plt.show()


    def export_output(self, path: str): #TODO: json_path as a input parameters!! -> Changes' been done!
        #json_path = "output_data.json" #TODO: move to json file
        
        json_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/" + path + ".json"
        try:
            with open(json_path, 'r') as file:
                output_data = json.load(file)
                
        except FileNotFoundError:
            output_data = {}
            
        output_data.setdefault('real_sensor_output', []).append(self.sensor_out)
        output_data.setdefault('virtual_sensor_output', []).append(self.vs_sensor_out)

        local_time = time.localtime()
        output_data.setdefault('time', []).append(time.strftime("%y-%m-%d %H:%M:%S", local_time))

        with open(self.dt_path, 'r') as f:
            dt_params = json.load(f)
        output_data.setdefault('Input_parameter', []).append(dt_params[0]["parameters"]["E"])

        with open(json_path, 'w') as file:
            json.dump(output_data, file)
            
        return json_path
    
    def fields_assignment(self, data):
        if data == None:
            pass
        
        else:
            for i in data.keys():
                if i == "displacement":
                    self.problem.fields.displacement = data[i]
                elif i == "temperature":
                    self.problem.fields.temperature = data[i]
        
    def fields_data_storer(self, path):
        data_to_store = {}

        for i in dir(self.problem.fields):
            if not i.startswith("_"):
                k = getattr(self.problem.fields, i)
                if k:
                    data_to_store[i] = k.x.array[:]
        try:
            pkl_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/" + path
            with open(f"{pkl_path}_params.pkl", "wb") as f:
                pickle.dump(data_to_store, f)
                
        except Exception as e:
            print(f"An error occurred while saving the model: {e}")
            
            


#%%
    
if __name__ == "__main__": 
    
    model_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh'
    
    model_parameters = {'model_name': 'displacements',
     'df_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv',
     'meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json',
     'MKP_meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json',
     'MKP_translated_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json',
     'virtual_sensor_added_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json',
     'cache_path': '',
     'paraview_output': True,
     'paraview_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview',
     'material_parameters': {'E': 40000000000000.0, 'nu': 0.2, 'rho': 2350},
     'tension_z': 0.0,
     'mass': 50000.0,
     'g': 9.81,
     'initial_position': [0.0, 0.0, 0.0],
     'speed': 1.0,
     'length': 7.5,
     'width': 2.5,
     'height': 6.5,
     'length_road': 95.0,
     'width_road': 14.0,
     'thickness_deck': 0.2,
     'dt': 30.0,
     'reference_temperature': 300,
     'temperature_coefficient': 1e-05,
     'temperature_alpha': 1e-05,
     'temperature_difference': 5.0,
     'reference_height': -2.5,
     'boundary_conditions': {'bc1': {'model': 'clamped_edge',
       'side_coord_1': 0.0,
       'coord_1': 2,
       'side_coord_2': 0.0,
       'coord_2': 1},
      'bc2': {'model': 'clamped_edge',
       'side_coord_1': 95.185,
       'coord_1': 2,
       'side_coord_2': 0.0,
       'coord_2': 1}}}
    
    dt_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'
    
    
    dm = DisplacementModel(model_path, model_parameters, dt_path)
    dm.solve()
