import json

from nibelungenbruecke.scripts.postprocessing.posterior_predictive import posterior_predictive

def task_posterior_predictive():
    postprocess_parameters_path = "input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)
        # TODO: Add targets for the histogram plots

    posterior_predictive_parameters = postprocess_parameters["posterior_predictive"]
    return {'actions': [(posterior_predictive,[],{'parameters':posterior_predictive_parameters})],
            'file_dep': [posterior_predictive_parameters["model_path"],posterior_predictive_parameters["inference_data_path"]],
            'targets': [posterior_predictive_parameters["output_parameters"]["output_path"]+posterior_predictive_parameters["output_parameters"]["output_format"]],
            'uptodate': [True]}

if __name__ == "__main__":

    postprocess_parameters_path = "input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)

    posterior_predictive(postprocess_parameters["posterior_predictive"])