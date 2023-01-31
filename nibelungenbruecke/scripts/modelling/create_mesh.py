import gmsh
# import os
# import sys

# # Get the parent directory of the current script
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # Add the parent directory to sys.path
# sys.path.append(root_path)

from nibelungenbruecke.scripts.utilities.checks import check_path_exists

def create_mesh(parameters):
    "Creates the cross section of the Nibelungenbrücke from a set of parameters"
    
    # Import parameters
    mesh_parameters = _get_default_parameters()
    for key, value in parameters.items():
        mesh_parameters[key] = value

    # Sanity checks
    check_path_exists(mesh_parameters["geometry_path"]+mesh_parameters["geometry_format"])

    # Initialize gmsh
    gmsh.initialize()

    # Define the habitual meshing parameters
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_parameters["characteristic_length_min"])
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_parameters["characteristic_length_max"])
    
    # Import the .geo_unrolled file
    gmsh.open(mesh_parameters["geometry_path"]+mesh_parameters["geometry_format"])
    gmsh.model.geo.synchronize()

    # Perform the meshing
    gmsh.model.mesh.generate(mesh_parameters["mesh_dimension"])

    # Save the mesh to a .msh file
    gmsh.write(mesh_parameters["output_path"]+".msh")

    # Finalize gmsh
    gmsh.finalize()

def _get_default_parameters():

    default_parameters = {
        "geometry_path": "input/models/geometry",
        "geometry_format": ".geo_unrolled",
        "characteristic_length_min": 1.0,
        "characteristic_length_max": 2.0,
        "mesh_dimension":3,
        "output_path": "input/models/mesh",
    }

    return default_parameters