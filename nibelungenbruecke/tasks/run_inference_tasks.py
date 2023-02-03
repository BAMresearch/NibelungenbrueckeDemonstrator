import json

from nibelungenbruecke.scripts.inference.run_inference_problem import run_inference_problem

def task_run_inference_problem():
    inference_parameters_path = "input/settings/inference_parameters.json"
    with open(inference_parameters_path, 'r') as f:
        inference_parameters = json.load(f)
        targets = []
        if inference_parameters["postprocessing"]["pair_plot"]:
            targets.append(inference_parameters["postprocessing"]["output_pair_plot"]+inference_parameters["postprocessing"]["pair_plot_format"])
        if inference_parameters["postprocessing"]["posterior_plot"]:
            targets.append(inference_parameters["postprocessing"]["output_posterior_plot"]+inference_parameters["postprocessing"]["posterior_plot_format"])
        if inference_parameters["postprocessing"]["trace_plot"]:
            targets.append(inference_parameters["postprocessing"]["output_trace_plot"]+inference_parameters["postprocessing"]["trace_plot_format"])
        targets.append(inference_parameters["output_parameters"]["output_path"]+inference_parameters["output_parameters"]["output_format"])
    
    return {'actions': [(run_inference_problem,[],{'parameters':inference_parameters})],
            'file_dep': [inference_parameters["model_path"]],
            'targets': targets,
            'uptodate': [True]}

if __name__ == "__main__":

    inference_parameters_path = "input/settings/inference_parameters.json"
    with open(inference_parameters_path, 'r') as f:
        inference_parameters = json.load(f)
        
    run_inference_problem(inference_parameters)