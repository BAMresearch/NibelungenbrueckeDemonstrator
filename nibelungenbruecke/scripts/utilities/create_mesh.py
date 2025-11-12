import gmsh

from nibelungenbruecke.scripts.utilities.checks import check_path_exists

def create_mesh(parameters):
    "Creates the cross section of the Nibelungenbrücke from a set of parameters"
    
    # Import parameters
    mesh_parameters = _get_default_parameters()
    for key, value in parameters.items():
        mesh_parameters[key] = value

    # Sanity checks
    pre_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/"
    check_path_exists(pre_path + mesh_parameters["geometry_path"]+mesh_parameters["geometry_format"])

    # Initialize gmsh
    gmsh.initialize()

    # Define the habitual meshing parameters
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_parameters["characteristic_length_min"])
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_parameters["characteristic_length_max"])
    
    # Import the .geo_unrolled file
    gmsh.open(pre_path+mesh_parameters["geometry_path"]+mesh_parameters["geometry_format"])
    gmsh.model.geo.synchronize()
    
    # Optional: add physical groups programmatically
    surface_tags = gmsh.model.getEntities(dim=2)
    gmsh.model.addPhysicalGroup(2, [s[1] for s in surface_tags], name="span_surface")
    
    line_tags = gmsh.model.getEntities(dim=1)
    gmsh.model.addPhysicalGroup(1, [l[1] for l in line_tags], name="edges")


    # Perform the meshing
    gmsh.model.mesh.generate(mesh_parameters["mesh_dimension"])

    # Save the mesh to a .msh file
    gmsh.write(pre_path+mesh_parameters["output_path"]+".msh")

    # Finalize gmsh
    gmsh.finalize()

def _get_default_parameters():

    default_parameters = {
        "geometry_path": "input/models/cross_section_pilot",
        "geometry_format": ".geo_unrolled",
        "characteristic_length_min": 1.0,
        "characteristic_length_max": 2.0,
        "mesh_dimension":2,
        "output_path": "input/models/2d_pilot_mesh",
    }

    return default_parameters


##

if __name__ == "__main__":
    import json
    json_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/model_parameters_2d_pilot.json"
    with open(json_path, "r") as f:
        parameters = json.load(f)
    create_mesh(parameters)