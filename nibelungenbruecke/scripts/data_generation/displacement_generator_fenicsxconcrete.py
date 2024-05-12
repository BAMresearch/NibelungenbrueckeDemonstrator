import ufl
from petsc4py.PETSc import ScalarType
from dolfinx import fem
import dolfinx as df
import json
import numpy as np
from fenicsxconcrete.finite_element_problem.linear_elasticity import LinearElasticity
from fenicsxconcrete.util import ureg
from mpi4py import MPI
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
from nibelungenbruecke.scripts.data_generation.nibelungen_experiment import NibelungenExperiment
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request, MetadataSaver, Translator
class GeneratorFeniCSXConcrete(GeneratorModel):
    """
    A class for generating FEniCS-X Concrete-based models and handling data generation.

    Parameters:
        model_path (str): Path to the model.
        sensor_positions_path (str): Path to the sensor positions.
        model_parameters (dict): Model parameters.
        output_parameters (dict): Output parameters (optional).
    """

    def __init__(self, model_path: str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):
        super().__init__(model_path, sensor_positions_path, model_parameters, output_parameters)
        self.material_parameters = self.model_parameters["material_parameters"] # Default empty dict!!
          
    def LoadGeometry(self):
        ''' Load the meshed geometry from a .msh file'''
        pass
    
    def GenerateModel(self):
        """Generate the model based on the provided parameters."""
        self.experiment = NibelungenExperiment(self.model_path, self.material_parameters)
        default_p = self._get_default_parameters()
        default_p.update(self.experiment.default_parameters())
        self.problem = LinearElasticity(self.experiment, default_p)

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


#
    
api = API_Request()
api.fetch_data()
print(api.df)