import ufl
from petsc4py.PETSc import ScalarType
from dolfinx import fem
import dolfinx
from mpi4py import MPI
from fenicsxconcrete.util import ureg

from nibelungenbruecke.scripts.utilities.checks import assert_path_exists

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
        assert_path_exists(model_path)
        self.model_path = model_path
        assert_path_exists(model_parameters)
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

