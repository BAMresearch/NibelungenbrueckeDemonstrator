import dolfinx
from mpi4py import MPI
import dolfinx as df
import json

from nibelungenbruecke.scripts.utilities.checks import assert_path_exists
from nibelungenbruecke.scripts.utilities.loaders import load_sensors
from nibelungenbruecke.scripts.utilities.offloaders import offload_sensors


from nibelungenbruecke.scripts.data_generation.nibelungen_experiment import NibelungenExperiment
from fenicsxconcrete.finite_element_problem.linear_elasticity import LinearElasticity
from fenicsxconcrete.util import ureg
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request, MetadataSaver, Translator

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
    
    @staticmethod
    def _get_default_parameters():
        ''' Get the default parameters for the model'''
        raise NotImplementedError("_get_default_parameters should be implemented")
    """        


#%%
class DisplacementModel(BaseModel):
    
    def __init__(self, model_path: str, model_parameters: dict):
        super().__init__(model_path, model_parameters)
        self.material_parameters = self.model_parameters["material_parameters"]
        self.default_p = self._get_default_parameters()
        
    def LoadGeometry(self):
        pass
    
    def GenerateModel(self):
        self.experiment = NibelungenExperiment(self.model_path, self.material_parameters)
        self.default_p.update(self.experiment.default_parameters())
        self.problem = LinearElasticity(self.experiment, self.default_p)
        print("GenerateModel has succesfully run!")
        
    def GenerateData(self):
        """Generate data based on the model parameters."""

        api_request = API_Request()
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

        """
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement)
        print("GenerateData has succesfully run after the paraview part!")
        """
        
        
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

#%%

class Model:
    def __init__(self, model_path, model_parameters):
        self.DM = DisplacementModel(model_path, model_parameters)
        
    def reinitialize(self):
        self.DM.LoadGeometry()
        self.DM.GenerateModel()
        self.DM.GenerateData()    
    
    def update_input(self, sensor_input):
        if isinstance(sensor_input, (int, float)):
            self.DM.default_p["E"] = sensor_input * ureg("N/m^2")
            #self.sensor_in = sensor_input
            return True
        else:
            return False
        
    def solve(self):
        self.reinitialize()
        self.sensor_out = self.DM.api_dataFrame['E_plus_445LVU_HS--u-_Avg1'].iloc[-1]
        
        file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
        with open(file_path, 'r') as file:
            vs_data = json.load(file)
        
        self.vs_sensor_out = vs_data['virtual_sensors']['E_plus_445LVU_HS--u-_Avg1']['displacements'][-1][0]
        
    def export_output(self):
        json_path = "output_data.json"
        
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
class  DigitalTwin:
    def __init__(self, model_path, model_parameters):
        self.model = Model(model_path, model_parameters)
        
    def predict(self, input_value):
        if self.model.update_input(input_value):
            self.model.solve()
            return self.model.export_output()
        else:
            return None
    
        
#%%

class Ocrhestrator:
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
        

#%%


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


o = Ocrhestrator()
dt = DigitalTwin(model_path, model_parameters)
o.predict_dt(dt, 2)
#o.predict_last_week(digital_twin, inputs)
#o.compare(output, input_value)


"""
if __name__ == "__main__":
    d = DisplacementModel(model_path, model_parameters)
    d.LoadGeometry()
    print()
    print("first part")
    print()
    d.GenerateModel()
    print()
    print("second part")
    print()
    d.GenerateData()
    print()
    print("third part")
    print()   
    #d.problem.sensors.get('E_plus_413TU_HSS-m-_Avg1', None).data[0].tolist()

 
"""      