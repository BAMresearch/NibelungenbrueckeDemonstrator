import ufl
from petsc4py.PETSc import ScalarType
from dolfinx import fem
import dolfinx as df

from fenicsxconcrete.finite_element_problem.linear_elasticity import LinearElasticity
from fenicsxconcrete.util import ureg

from mpi4py import MPI
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
from nibelungenbruecke.scripts.data_generation.nibelungen_experiment import NibelungenExperiment
from nibelungenbruecke.scripts.utilities.sensor_translators import Translator

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
        #Generating Translator object
        T = Translator(self.sensor_positions)
        
        # Translation from MKP data format (currently supports "move" operations only!)
        _, meta_output_path = T.translator_to_sensor(self.model_parameters["df_output_path"], self.model_parameters["meta_output_path"]) 

        self.problem.import_sensors_from_metadata(meta_output_path)
        self.problem.solve()

        #Paraview output
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement)

       # Reverse translation to MKP data format
        T.translator_to_MKP(self.problem, self.model_parameters["save_to_MKP_path"])

    @staticmethod
    def _get_default_parameters():
        default_parameters = {
            "rho":7750 * ureg("kg/m^3"),
            "E":210e9 * ureg("N/m^2"),
            "nu":0.28 * ureg("")
        }
        return default_parameters
    
