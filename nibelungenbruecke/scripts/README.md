In this folder, the python scripts run by the tasks are located.
- `modelling` contains the scripts to generate the cross-section, 3D geometry and mesh of the Nibelungenbrücke.
- `data_generation` contains the scripts required for generating synthetic data out of a meshed geometrical model.
- `inference` contains the scripts to run a Bayesian inference procedure on a model provided with measurements data.
- `postprocessing` includes scripts used to post-process the results, run posterior-predictive queries and generate graphs and documentation.
- `preprocessing` includes scripts that treat the data to be provided to the inference model.
- `utilities` contains general utilities that may be used in more than one of the previous categories or that generally simplify the code.