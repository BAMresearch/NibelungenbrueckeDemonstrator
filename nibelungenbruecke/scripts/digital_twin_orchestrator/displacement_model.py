from nibelungenbruecke.scripts.digital_twin_orchestrator.base_model import BaseModel
#from base_model import BaseModel
import dolfinx as df
import json
from nibelungenbruecke.scripts.data_generation.nibelungen_experiment import NibelungenExperiment
from fenicsxconcrete.finite_element_problem.linear_elasticity import LinearElasticity
from fenicsxconcrete.util import ureg
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request, MetadataSaver, Translator
from nibelungenbruecke.scripts.utilities.loaders import load_sensors
from nibelungenbruecke.scripts.utilities.offloaders import offload_sensors
import importlib

class DisplacementModel(BaseModel):
    
    def __init__(self, model_path: str, model_parameters: dict, dt_path: str):
        super().__init__(model_path, model_parameters)
        
        self.material_parameters = self.model_parameters["material_parameters"]
        self.default_p = self._get_default_parameters()
        self.dt_path = dt_path
        self.vs_path = self.model_parameters["material_parameters"]
        
    def LoadGeometry(self):
        pass
    
    def GenerateModel(self):
        self.experiment = NibelungenExperiment(self.model_path, self.material_parameters)
        self.default_p.update(self.experiment.default_parameters())
        self.problem = LinearElasticity(self.experiment, self.default_p)
        
    def GenerateData(self):
        """Generate data based on the model parameters."""

        self.api_request = API_Request()
        self.api_dataFrame = self.api_request.fetch_data()

        metadata_saver = MetadataSaver(self.model_parameters, self.api_dataFrame)
        metadata_saver.saving_metadata()

        translator = Translator(self.model_parameters)
        translator.translator_to_sensor()

        self.problem.import_sensors_from_metadata(self.model_parameters["MKP_meta_output_path"])
        self.problem.fields.temperature = self.problem.fields.displacement #!!
        self.problem.solve()

        translator.save_to_MKP(self.api_dataFrame)
        translator.save_virtual_sensor(self.problem)

        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement)
        
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
    
    def update_input(self, sensor_input):
        
        with open(self.dt_path, 'r') as f:
            dt_params = json.load(f)
        
        # currently, only updates E value
        #TODO: Make this part more automated/flexible!  
        if isinstance(sensor_input, (int, float)):
            dt_params[0]["parameters"]["E"] = sensor_input
            
            with open(self.dt_path, 'w') as file:
                json.dump(dt_params, file, indent=4)
            return True
        else:
            return False
        
    def solve(self):

        self.LoadGeometry()
        self.GenerateModel()
        self.GenerateData()
        
        #TODO: API Request output error!!
        self.sensor_out = self.api_dataFrame['E_plus_080DU_HSN-u-_Avg1'].iloc[-1] # *1000 #Convertion from meter to milimeter
        #self.sensor_out = self.api_dataFrame['E_plus_413TU_HSS-m-_Avg1'].iloc[-1]
   
        
        vs_file_path = self.model_parameters["virtual_sensor_added_output_path"]
        with open(vs_file_path, 'r') as file:
            self.vs_data = json.load(file)        
        
        #TODO: API Request output error!!
        #self.vs_sensor_out = self.vs_data['virtual_sensors']['E_plus_413TU_HSS-m-_Avg1']['displacements'][-1][0]
        self.vs_sensor_out = self.vs_data['virtual_sensors']['E_plus_080DU_HSN-u-_Avg1']['displacements'][-1][0]
        
    def export_output(self): #TODO: json_path as a input parameters!!
        json_path = "output_data.json" #TODO: move to json file
        
        try:
            with open(json_path, 'r') as file:
                output_data = json.load(file)
                
        except FileNotFoundError:
            output_data = {}
            
        output_data.setdefault('real_sensor_output', []).append(self.sensor_out)
        output_data.setdefault('virtual_sensor_output', []).append(self.vs_sensor_out)
        
        with open(json_path, 'w') as file:
            json.dump(output_data, file)
            
        return json_path
 