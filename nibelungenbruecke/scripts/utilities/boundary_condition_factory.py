import importlib

def boundary_condition_factory(mesh, function, V, bc_parameters):
    # Import the function from the library with bcs
    module = importlib.import_module("nibelungenbruecke.scripts.utilities.boundary_conditions")
    function_bc = getattr(module, function)

    # Create an instance of the derived class with the given parameters
    return function_bc(mesh, V, bc_parameters)