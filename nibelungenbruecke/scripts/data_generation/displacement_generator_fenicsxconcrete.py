import ufl
from petsc4py.PETSc import ScalarType
from dolfinx import fem
import dolfinx as df
import json

from fenicsxconcrete.finite_element_problem.linear_elasticity import LinearElasticity
from fenicsxconcrete.util import ureg

from mpi4py import MPI
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
from nibelungenbruecke.scripts.data_generation.nibelungen_experiment import NibelungenExperiment
#from nibelungenbruecke.scripts.utilities.sensor_translators import Translator
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_request
from nibelungenbruecke.scripts.utilities.API_sensor_storing import saveAPI
from nibelungenbruecke.scripts.utilities.API_sensor_translator import Translator


class GeneratorFeniCSXConcrete(GeneratorModel):
    def __init__(self, model_path: str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):
        super().__init__(model_path, sensor_positions_path, model_parameters, output_parameters)
        self.material_parameters = self.model_parameters["material_parameters"] # currently it is an empty dict!!
          
    def LoadGeometry(self):
        ''' Load the meshed geometry from a .msh file'''
        pass
    
    def GenerateModel(self):
        self.experiment = NibelungenExperiment(self.model_path, self.material_parameters)

        default_p = self._get_default_parameters()
        default_p.update(self.experiment.default_parameters())
        self.problem = LinearElasticity(self.experiment, default_p)
    
    def GenerateData(self):
    
        meta_output_path = self.model_parameters["meta_output_path"]
        df_output_path = self.model_parameters["df_output_path"]
        MKP_meta_output_path = self.model_parameters["MKP_meta_output_path"]

        api_request = API_request()
        api_dataFrame = api_request.API()

        savingData = saveAPI(meta_output_path, api_dataFrame, df_output_path)
        savingData.save()

        T = Translator(meta_output_path)
        T.translator_to_sensor(MKP_meta_output_path)

        ## newer methods and modules!!!

        self.problem.import_sensors_from_metadata(MKP_meta_output_path)
        self.problem.solve()

        #Paraview output
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement)
#%%
        
        
        """
        print(f"burda biseyler oldu mu?:: {self.problem.fields.displacement}")
        print("###########################################################################################################")
        print(self.problem.sensors["DisplacementSensor"].data)
        
        VS_result_path = '/home/msoenmez/Desktop/workspce/API/vs_output.json'
        displacement_value = self.problem.fields.displacement()  # Call the function to get the value

        data = {"displacement": displacement_value}

        with open(VS_result_path, "w") as json_file:
            json.dump(data, json_file, indent=2)

        """
#%%

       # Reverse translation to MKP data format
        #T.translator_to_MKP(self.problem, self.model_parameters["save_to_MKP_path"])

    @staticmethod
    def _get_default_parameters():
        default_parameters = {
            "rho":7750 * ureg("kg/m^3"),
            "E":210e9 * ureg("N/m^2"),
            "nu":0.28 * ureg("")
        }
        return default_parameters
    