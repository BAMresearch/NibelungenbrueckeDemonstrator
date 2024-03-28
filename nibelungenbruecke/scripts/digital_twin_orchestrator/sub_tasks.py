# dodo_runner.py

import json
import importlib
from doit.doit_cmd import DoitMain
from doit.cmd_base import ModuleTaskLoader
import sys
from nibelungenbruecke.scripts.utilities import checks

def run_dodo():
    ### CONFIG TASKS ###
    doit_parameters_path = "input/settings/doit_parameters.json"
    checks.assert_path_exists(doit_parameters_path)

    with open(doit_parameters_path, 'r') as file:
        DOIT_CONFIG = json.load(file)

    # Import all tasks specified in the JSON file marked as true
    for task, load_task in DOIT_CONFIG.items():
        if load_task:
            module = importlib.import_module("nibelungenbruecke.tasks." + task + "_tasks")
            functions = {name: value for name, value in vars(module).items() if callable(value)and name.startswith("task_")}
            for name, value in functions.items():
                globals()[name] = value

    # Run tasks if __name__ == '__main__'
    DoitMain(ModuleTaskLoader(globals())).run(sys.argv[1:])

# Run the function if __name__ == '__main__'
if __name__ == "__main__":
    run_dodo()
