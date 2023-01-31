These are the tasks that can be called by PyDoit:
- `generate_synthetic_data_tasks`: Generates synthetic data from a given model to train or fit another one. For demonstration or surrogate purposes.
- `generate_model_tasks`: Generates the geometry and mesh for the Nibelungenbrücke according to a set of predefined parameters.
- `preprocess_data_tasks`: Preprocess the data from a database for inference. To preprocess for predictions, use the tasks in `query_posterior_predictive_tasks`.
- `run_inference_tasks`: Tasks that govern the inference procedure to adapt the Digital Twin (DT) to a given dataset.
- `postprocess_results_tasks`: Postprocess the results obtained in the inference procedure.
- `generate_document_tasks`: Generates a LaTeX document with the results of the inference problem.
- `query_posterior_predictive_tasks`: Queries a prediction for the calibrated model based on a given input. The output is postprocess and results are generated.