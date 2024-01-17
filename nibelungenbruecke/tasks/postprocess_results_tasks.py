import json

from nibelungenbruecke.scripts.postprocessing.plot_influence_lines import plot_influence_lines

def task_plot_influence_lines():
    postprocess_parameters_path = "./input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)

    plot_influence_lines_parameters = postprocess_parameters["plot_influence_lines"]
    return {'actions': [(plot_influence_lines,[],{'parameters':plot_influence_lines_parameters})],
            'file_dep': [plot_influence_lines_parameters["sensors_path"],plot_influence_lines_parameters["influence_lines_path"]],
            'targets': [plot_influence_lines_parameters["output_path"]+plot_influence_lines_parameters["output_format"]],
            'uptodate': [True]}

if __name__ == "__main__":

    postprocess_parameters_path = "./input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)

    plot_influence_lines(postprocess_parameters["plot_influence_lines"])