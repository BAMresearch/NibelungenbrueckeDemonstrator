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


from nibelungenbruecke.scripts.data_generation.generate_data import generate_data
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
from nibelungenbruecke.scripts.data_generation.displacement_generator_fenicsxconcrete import GeneratorFeniCSXConcrete

model_path = "./input/models/mesh.msh"
sensor_positions_path = "./input/sensors/20230215092338.json"
model_parameters =  {
            "model_name": "displacements",
            "df_output_path":"./input/sensors/API_df_output.csv",
            "meta_output_path":"./input/sensors/API_meta_output.json",
            "MKP_meta_output_path":"./output/sensors/MKP_meta_output.json",
            "MKP_translated_output_path":"./output/sensors/MKP_translated.json",
            "virtual_sensor_added_output_path":"./output/sensors/virtual_sensor_added_translated.json",
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

        

class OrchestratorDisplacement(GeneratorFeniCSXConcrete):
    def __init__(self, model_path: str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):
        super().__init__(model_path, sensor_positions_path, model_parameters, output_parameters)
        self.material_parameters = self.model_parameters["material_parameters"] # Default empty dict!!
        
            
class Model:
    def __init__(self, SimulationModel):
        self.SimulationModel = SimulationModel
        self.sensor_in = 0.0
        self.sensor_out = 0.0
        self.parameter = 2.0

    def update_input(self, sensor_input):
        if isinstance(sensor_input, (int, float)):
            self.sensor_in = sensor_input
            return True
        else:
            return False
        
    def solve(self):
        self.sensor_out = self.parameter * self.sensor_in
        return True
    
    def export_output(self):
        return self.sensor_out

    def test(self):
        self.a = self.SimulationModel.model_path
        self.GenerateModel = self.SimulationModel.GenerateModel()


        
model = Model(OrchestratorDisplacement(model_path, sensor_positions_path, model_parameters))
model.test()
print(model.a)
print(model.GenerateModel.problem)




        