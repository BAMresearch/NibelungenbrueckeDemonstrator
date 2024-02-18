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
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_request
from nibelungenbruecke.scripts.utilities.API_sensor_storing import saveAPI
from nibelungenbruecke.scripts.utilities.API_sensor_translator import Translator


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

    def save_displacement_values(self, displacement_values):
        """
        Save displacement values corresponding to each sensor ID in the MKP_meta_output_path JSON file.

        Parameters:
            displacement_values: Displacement values.
        """
        with open(self.model_parameters["MKP_meta_output_path"], 'r') as f:
            metadata = json.load(f)

        virtual_sensors = []
        for sensor in metadata["sensors"]:
            sensor_id = sensor["id"]
            position = sensor["where"]
            displacement_value = displacement_values.sensors.get(sensor_id, None)
            if displacement_value is not None:
                displacement_value_list = displacement_value.data[0].tolist()  # Convert ndarray to list
                virtual_sensors.append({"id": sensor_id, "displacement": displacement_value_list})

        metadata["virtual_sensors"] = virtual_sensors

        with open(self.model_parameters["MKP_meta_output_path"], 'w') as f:
            json.dump(metadata, f, indent=4)

    def GenerateData(self):
        """Generate data based on the model parameters."""
        meta_output_path = self.model_parameters["meta_output_path"]
        df_output_path = self.model_parameters["df_output_path"]
        MKP_meta_output_path = self.model_parameters["MKP_meta_output_path"]

        api_request = API_request()
        api_dataFrame = api_request.API()

        savingData = saveAPI(meta_output_path, api_dataFrame, df_output_path)
        savingData.save()

        T = Translator(meta_output_path)
        T.translator_to_sensor(MKP_meta_output_path)

        self.problem.import_sensors_from_metadata(MKP_meta_output_path)
        self.problem.solve()

        self.save_displacement_values(self.problem)

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
