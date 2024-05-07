import ufl
from petsc4py.PETSc import ScalarType
from dolfinx import fem
import dolfinx
from mpi4py import MPI
from fenicsxconcrete.util import ureg

class BaseModel:
    ''' Base class for a generator of synthetic data from a model.'''

    """
    def __init__(self, model_path:str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):

        assert_path_exists(model_path)
        self.model_path = model_path

        assert_path_exists(sensor_positions_path)
        self.sensor_positions = sensor_positions_path

        default_parameters = self._get_default_parameters()
        for key, value in default_parameters.items():
            if key not in model_parameters:
                model_parameters[key] = value

        self.model_parameters = model_parameters
        self.output_parameters = output_parameters
    """   
    
    def __init__(self, model_path: str, model_parameters: dict):
        #assert_path_exists(model_path)
        self.model_path = model_path
        #assert_path_exists(model_parameters)
        self.model_parameters = model_parameters
    
    def Generate(self):
        ''' Generate the data from the start'''
        self.LoadGeometry()
        self.GenerateModel()
        self.GenerateData()

    def LoadGeometry(self):
        ''' Load the meshed geometry from a .msh file'''        
        # Translate mesh from gmsh to dolfinx
        self.mesh, cell_tags, facet_tags = dolfinx.io.gmshio.read_from_msh(self.model_path, MPI.COMM_WORLD, 0)
        # self.mesh = dolfinx.mesh.create_mesh(MPI.COMM_WORLD, mesh.points, mesh.cells)
        
    def GenerateModel(self):
        ''' Generate the FEM model.'''
        raise NotImplementedError("GenerateModel should be implemented")

    def GenerateData(self):
        ''' Run the FEM model and generate the data'''
        raise NotImplementedError("GenerateData should be implemented")
    
    def update_input(self, sensor_input):
        raise NotImplementedError("update_input should be implemented")
        
    def solve(self):
        raise NotImplementedError("solve should be implemented")
        
    def export_output(self):
        raise NotImplementedError("export_output should be implemented")

    """
    @staticmethod
    def sensor_offloader_wrapper(generate_data_func):
        ''' Wrapper to simplify sensor offloading'''
        
        def wrapper(self, *args, **kwargs):
            
            generate_data_func(self, *args, **kwargs)
            
            # Store the value at the sensors
            sensors = load_sensors(self.sensor_positions)
            for sensor in sensors:
                sensor.measure(self)

            # Output the virtual measurements to a file
            offload_sensors(sensors, self.output_parameters["output_path"]+"/"+self.model_parameters["model_name"], self.output_parameters["output_format"])
            
        return wrapper
    """    
    @staticmethod
    def _get_default_parameters():
        ''' Get the default parameters for the model'''
        raise NotImplementedError("_get_default_parameters should be implemented")



#%%


#from nibelungenbruecke.scripts.digital_twin_orchestrator.base_model import BaseModel
from base_model import BaseModel
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
        
    def LoadGeometry(self):
        pass
    
    def GenerateModel(self):
        self.experiment = NibelungenExperiment(self.model_path, self.material_parameters)
        self.default_p.update(self.experiment.default_parameters())
        self.problem = LinearElasticity(self.experiment, self.default_p)
        print("GenerateModel has succesfully run!")
        
    def GenerateData(self):
        """Generate data based on the model parameters."""

        api_request = API_Request()     #TODO: Include DU:dehnung sensor for vertical displacement!!
        self.api_dataFrame = api_request.fetch_data()

        metadata_saver = MetadataSaver(self.model_parameters, self.api_dataFrame)
        metadata_saver.saving_metadata()

        translator = Translator(self.model_parameters)
        translator.translator_to_sensor()

        self.problem.import_sensors_from_metadata(self.model_parameters["MKP_meta_output_path"])
        self.problem.fields.temperature = self.problem.fields.displacement #!!
        self.problem.solve()

        translator.save_to_MKP(self.api_dataFrame)
        translator.save_virtual_sensor(self.problem)
        print("GenerateData has succesfully run until the paraview part!")

        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement)
        print("GenerateData has succesfully run after the paraview part!")
        
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
        
        vs_file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
                
        self.LoadGeometry()
        self.GenerateModel()
        self.GenerateData()
        
        self.sensor_out = self.api_dataFrame['E_plus_445LVU_HS--u-_Avg1'].iloc[-1] #TODO: DU: dehnung sensor to import from API
                
        with open(vs_file_path, 'r') as file:
            self.vs_data = json.load(file)        
        self.vs_sensor_out = self.vs_data['virtual_sensors']['E_plus_445LVU_HS--u-_Avg1']['displacements'][-1][0]
        
    def export_output(self): #TODO: json_path as a input parameters!!
        json_path = "output_data.json" #TODO: move to json file
        
        try:
            with open(json_path, 'r') as file:
                output_data = json.load(file)
                
        except FileNotFoundError:
            output_data = {}
            
        output_data.setdefault('real_sensor_data', []).append(self.sensor_out)
        output_data.setdefault('virtual_sensor_data', []).append(self.vs_sensor_out)
        
        with open(json_path, 'w') as file:
            json.dump(output_data, file)
            
        return json_path
    
#%%
if __name__ == "__main__":
    model_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh"
    sensor_positions_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/20230215092338.json"
    model_parameters =  {
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
    output_parameters = {
            "output_path": "./input/data",
            "output_format": ".h5"}

    dt_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'


    DispModel = DisplacementModel(model_path, model_parameters, dt_path)
    DispModel.LoadGeometry()
    DispModel.GenerateModel()
    DispModel.GenerateData()
    
    vs_file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
    DispModel.solve(vs_file_path)
    
    DispModel.export_output()

#%%
if __name__ == "__main__":
    path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/generate_data_parameters.json"
    with open(path, "r") as file:
        data = json.load(file)
    model_path = data["model_path"]

    generation_list = data["generation_models_list"][0]
    sensor_positions_path = generation_list["sensors_path"]
    model_parameters = generation_list["model_parameters"]
    output_parameters = ""
    dt_path = generation_list["digital_twin_parameters_path"]

    DispModel = DisplacementModel(model_path, model_parameters, dt_path)
    DispModel.LoadGeometry()
    DispModel.GenerateModel()
    DispModel.GenerateData()
    
    vs_file_path = generation_list["virtual_sensor_added_output_path"]
    DispModel.solve(vs_file_path)
    DispModel.export_output()
    
    
#%%

from displacement_model import DisplacementModel
import json
import importlib

class  DigitalTwin:
    def __init__(self, model_path, model_parameters, path, model_to_run = "Displacement_1"):   #TODO: place path and model_to_run paramters into the JSON!!
        self.model_path = model_path
        self.model_parameters = model_parameters
        self.path = path
        self.model_to_run = model_to_run
        self.load_models()
        
    def load_models(self):
        with open(self.path, 'r') as json_file:
            self.models = json.load(json_file)
        
    def set_model(self):
        for model_info in self.models:
            if model_info["name"] == self.model_to_run:
                self.model_name = model_info["type"]
                self.object_name = model_info["class"]
                return True
        return False
    
    def predict(self, input_value):
        if self.set_model():
            module = importlib.import_module(self.model_name)
            digital_twin_model = getattr(module, self.object_name)(self.model_path, self.model_parameters, self.path)
            if digital_twin_model.update_input(input_value):
                digital_twin_model.solve()
                return digital_twin_model.export_output()
            
        return None
  
#%%

if __name__ == "__main__":
    model_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh"
    sensor_positions_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/20230215092338.json"
    model_parameters =  {
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
    output_parameters = {
            "output_path": "./input/data",
            "output_format": ".h5"}

    dt_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'


    DTM = DigitalTwin(model_path, model_parameters, dt_path)
    DTM.set_model()
    DTM.predict(3*10**9)
    DTM.GenerateData()
    
    vs_file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
    DTM.solve(vs_file_path)
    
    DTM.export_output()




#%%

#from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
from digital_twin import DigitalTwin

class Orchestrator:
    def __init__(self):
        self.updated = False
        
    def predict_dt(self, digital_twin, input_value):
        return digital_twin.predict(input_value)
    
    def predict_last_week(self, digital_twin, inputs):
        predictions = []
        for input_value in inputs:
            prediction = digital_twin.predict(input_value)
            if prediction is not None:
                predictions.append(prediction)
        return predictions

    def compare(self, output, input_value):
        self.updated = (output == 2 * input_value)

    def run(self, model_path, model_parameters, path, model_to_run, input_value=2.7*10**6):
        digital_twin = DigitalTwin(model_path, model_parameters, path, model_to_run)  # Assuming these parameters are available
        prediction = self.predict_dt(digital_twin, input_value)
        print("Prediction:", prediction)


#%%
if __name__ == "__main__":
    model_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh"
    sensor_positions_path = "/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/20230215092338.json"
    model_parameters =  {
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
    output_parameters = {
            "output_path": "./input/data",
            "output_format": ".h5"}

    dt_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'

    orch = Orchestrator()
    orch.run(model_path, model_parameters, dt_path, model_to_run= "Displacement_1")


