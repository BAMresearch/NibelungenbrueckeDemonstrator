import json
import numpy as np

from nibelungenbruecke.scripts.postprocessing.postprocessing_runner import postprocess_run

def task_postprocess_run():
    postprocess_parameters_path = "./input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)

    dependencies = list(np.concatenate([task["file_dep"] for task in postprocess_parameters.values()]).flat)
    return {'actions': [(postprocess_run,[],{'parameters':postprocess_parameters})],
            'file_dep': dependencies,
            'targets': [],
            'uptodate': [False]} # Normally always to be run