This folder contains the scripts required for generating synthetic data out of a meshed geometrical model.
- `generate_data.py` controls the data generation, allowing the creation of several datasets coming from different generator model in the same run based on a set of parameters and a list of models.
- `generator_model_factory.py` initializes the generator model indicated in the settings of the JSON file.
- `generator_model_base_class.py` is the base class for generating synthetic data. It contains general functionalities needed for the data generation and serves as basis for the derive generators.
- `displacement3D_generator.py` is a simple generator that models a static elastic FEM problem for a given set of material parameters and outputs the displacement at the sensor positions under self weight.