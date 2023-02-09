import json

from nibelungenbruecke.scripts.modelling.create_cross_section import create_cross_section3D
from nibelungenbruecke.scripts.modelling.create_geometry import create_geometry
from nibelungenbruecke.scripts.modelling.create_mesh import create_mesh

model_parameters_path = "./input/settings/model_parameters.json"
with open(model_parameters_path, 'r') as f:
    model_parameters = json.load(f)

def task_generate_cross_section():

    return {'actions': [(create_cross_section3D,[],{'parameters':model_parameters["cross_section"]})],
            'file_dep':[model_parameters_path],
            'targets': [model_parameters["cross_section"]["output_path"]+"_span"+model_parameters["cross_section"]["output_format"],
                        model_parameters["cross_section"]["output_path"]+"_pilot"+model_parameters["cross_section"]["output_format"]],
            'uptodate': [True]}

def task_generate_geometry():

    return {'actions': [(create_geometry,[],{'parameters':model_parameters["geometry"]})],
            'file_dep':[model_parameters["geometry"]["cross_section_path"]+"_span"+model_parameters["geometry"]["cross_section_format"],
                        model_parameters["geometry"]["cross_section_path"]+"_pilot"+model_parameters["geometry"]["cross_section_format"],
                        model_parameters_path],
            'targets': [model_parameters["geometry"]["output_path"]+model_parameters["geometry"]["output_format"]],
            'uptodate': [True]}

def task_generate_mesh():

    return {'actions': [(create_mesh,[],{'parameters':model_parameters["mesh"]})],
            'file_dep': [model_parameters["geometry"]["output_path"]+model_parameters["geometry"]["output_format"],
                        model_parameters_path],
            'targets': [model_parameters["mesh"]["output_path"]+".msh"],
            'uptodate': [True]}

if __name__ == "__main__":

    create_cross_section3D(model_parameters["cross_section"])
    create_geometry(model_parameters["geometry"])
    create_mesh(model_parameters["mesh"])
