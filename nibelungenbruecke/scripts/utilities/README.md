This folder contains general multipurpose utilities that generally simplify the code.
- `general_utilities.py` contains utilities that do not belong to any other group and can be used for multiple purposes.
- `checks.py` implements some checks and asserts in a human-readable format.
- `boundary_conditions.py` implements several boundary conditions in dolfinX.
- `boundary_conditions_factory.py` instantiates one of the boundary conditions from `boundary_conditions.py` as indicated in an input dictionary.
- `loaders.py` contains functions that can be used to load data from external files to variables or data structures.
- `offloaders.py` contains functions that can be used to export data to external files.
- `sensors.py` contains sensor definitions for the synthetic models as in FeniCsConcrete. In the future, they will be unified with probeye's sensor definitions.
- `probeye_utilities.py` contains function wrappers that allow to addapt probeye functions.
