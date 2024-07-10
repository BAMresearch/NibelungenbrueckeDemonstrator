from nibelungenbruecke.scripts.digital_twin_orchestrator.base_model import BaseModel

import tempfile
import shutil
import dolfinx
import numpy as np
from mpi4py import MPI

# Create a temporary directory for testing
temp_dir = tempfile.mkdtemp()

# Define a temporary model path and parameters for testing
temp_model_path = f"{temp_dir}/test_model.msh"
temp_model_parameters = {"param1": 1, "param2": 2}

# Create a dummy subclass of BaseModel for testing
class DummyModel(BaseModel):
    def GenerateModel(self):
        pass

    def GenerateData(self):
        pass

    def update_input(self, sensor_input):
        pass

    def solve(self):
        pass

    def export_output(self):
        pass

    @staticmethod
    def _get_default_parameters():
        return {"param1": 0, "param2": 0}

# Test BaseModel initialization
def test_initialization():
    print("\nTesting BaseModel initialization...")
    base_model = BaseModel(temp_model_path, temp_model_parameters)
    assert base_model.model_path == temp_model_path
    assert base_model.model_parameters == temp_model_parameters

# Test LoadGeometry method
def test_load_geometry():
    print("\nTesting LoadGeometry method...")
    dummy_model = DummyModel(temp_model_path, temp_model_parameters)
    dummy_model.LoadGeometry()
    assert isinstance(dummy_model.mesh, dolfinx.Mesh)

# Test Generate method
def test_generate():
    print("\nTesting Generate method...")
    dummy_model = DummyModel(temp_model_path, temp_model_parameters)
    dummy_model.Generate()

# Test _validate_parameters method
def test_validate_parameters():
    print("\nTesting _validate_parameters method...")
    base_model = BaseModel(temp_model_path, {})
    assert base_model.model_parameters == {"param1": 0, "param2": 0}

# Run tests
test_initialization()
test_load_geometry()
test_generate()
test_validate_parameters()

# Cleanup temporary directory
shutil.rmtree(temp_dir)
