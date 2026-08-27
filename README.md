# NibelungenbrueckeDemonstrator

The goal of **NibelungenbrueckeDemonstrator** is to provide a representative and repeatable workflow for the implementation of a stochastic [Digital Twin (DT)](https://en.wikipedia.org/wiki/Digital_twin) of the [Nibelungenbrücke in Worms (Germany)](https://de.wikipedia.org/wiki/Nibelungenbr%C3%BCcke_Worms). This repository has been developed by [_Bundesanstalt für Materialforschung und -prüfung (BAM)_](https://www.bam.de) in the context of the project "Data driven model adaptation for identifying stochastic digital twins of bridges", englobed in the funding initiative SPP 2388/1 100plus of the German Research Foundation (DFG).

The demonstrator is used through an **online, simulation-based digital twin**: an orchestration layer takes a dictionary of user inputs (physical model, simulation time window, virtual sensor locations, data source) , retrieves the environmental data for that window from an external API, runs a FEniCSx/[FenicsXConcrete](https://github.com/BAMresearch/FenicsXConcrete) simulation of the bridge, and returns time series at the requested locations together with the full-field response. Optionally, the same workflow runs with uncertainty quantification (UQ), so that predictions come with confidence information. This workflow is driven from the two Jupyter notebooks in the repository root, [J4NFDI_interface.ipynb](J4NFDI_interface.ipynb) and [3D_View_interface.ipynb](3D_View_interface.ipynb).

Due to its modular structure and user-oriented approach, this demonstrator can also be used as the basis for implementing the workflow of any digital twin using a [Bayesian framework](https://en.wikipedia.org/wiki/Bayesian_inference). This repository abides by the principles of [FAIR](https://www.go-fair.org/fair-principles/) (Findable, Accessible, Interoperable and Reusable) scientific software.

## Table of Contents

- [Bridge description](#bridge-description)
  - [Location](#location)
  - [Structure](#structure)
  - [Materials](#materials)
- [Quick start](#quick-start)
  - [Environment](#environment)
  - [Installation](#installation)
  - [Running the demonstrator](#running-the-demonstrator)
- [Notebook interfaces](#notebook-interfaces)
  - [J4NFDI_interface.ipynb](#j4nfdi_interfaceipynb)
  - [3D_View_interface.ipynb](#3d_view_interfaceipynb)
- [The Orchestrator API](#the-orchestrator-api)
  - [Simulation parameters](#simulation-parameters)
  - [Available models](#available-models)
  - [Data sources and API keys](#data-sources-and-api-keys)
  - [Methods](#methods)
- [Results and outputs](#results-and-outputs)
  - [Sensor plots](#sensor-plots)
  - [Full-field response](#full-field-response)
  - [Output files](#output-files)
- [Coordinate system and units](#coordinate-system-and-units)
- [Extending the demonstrator](#extending-the-demonstrator)
- [Legacy: doit inference workflow](#legacy-doit-inference-workflow)
  - [Running the basic example](#running-the-basic-example)
  - [Modifying the settings](#modifying-the-settings)
  - [Input and output data formating](#input-and-output-data-formating)
- [Integration in a larger Digital Twin](#integration-in-a-larger-digital-twin)
- [TO-DO](#to-do)

# Bridge description
## Location
Located in the city of [Worms](https://en.wikipedia.org/wiki/Worms,_Germany) (Rheinland-Palatinate), the Nibelungenbrücke connects it across the river Rhine with the cities of [Lampertheim](https://en.wikipedia.org/wiki/Lampertheim) and [Bürstadt](https://en.wikipedia.org/wiki/B%C3%BCrstadt) (Hesse).
It is the only road bridge between Mannheim in the south and Mainz in the north, which leads to the transit of 23000 vehicles every 24h on average.

The DT implemented in this repository focuses on the span closest to the west shore of the Rhein (Worms side) of the ["old" Nibelungenbrücke](https://structurae.net/en/structures/nibelungenbrucke). The measurements and dimensions of the bridge are provided by the organization of the SPP 2388/ 100plus program.

*INSERT PICTURES HERE?*
## Structure
The bridge is a [box girder bridge](https://en.wikipedia.org/wiki/Box_girder_bridge) built following the [balanced cantilever method](https://en.wikipedia.org/wiki/Cantilever_bridge).

*INSERT CROSS-SECTION DRAWINGS HERE?*
## Materials
The bridge is built out of prestressed concrete for the deck and reinforced concrete for piers and abutments. This demonstrator implements a simulation of the deck, with the following material parameters:

*INSERT TABLE WITH MATERIAL PARAMETERS*

# Quick start
## Environment
The demonstrator requires a FEniCSx environment. The reference environment is defined in [binder/environment.yml](binder/environment.yml) (conda environment `fenicsx-env`, Python 3.10, `fenics-dolfinx` 0.6.0, `gmsh`, `h5py`, `pyvista`, `meshio`, `pvlib`, `arviz`, plus pip installs of [FenicsXConcrete](https://github.com/BAMresearch/FenicsXConcrete) (branch `my-grf`), [probeye](https://github.com/BAMresearch/probeye), `chaospy`, `doit` and the Open-Meteo client packages):

```
mamba env create -f binder/environment.yml
conda activate fenicsx-env
```

[binder/Dockerfile](binder/Dockerfile) builds the same environment as a Jupyter image (based on `quay.io/jupyter/base-notebook`) for Binder or a JupyterHub deployment, and registers the `fenicsx-env` kernel under the display name *Python (fenicsx-env)*. On a JupyterHub instance where the environment was not built from the YAML file, the first (commented-out) code cell of each notebook installs the required packages with `pip` instead.

For inspecting the full-field results outside the notebook, [ParaView](https://www.paraview.org/) is recommended.

## Installation
From the root of the cloned repository, install the folder as a package using pip:
```
pip install .
```
Now the contents in `nibelungenbruecke` are available for their use in any Python script calling `import nibelungenbruecke`.

## Running the demonstrator
Start Jupyter **from the repository root** and open [J4NFDI_interface.ipynb](J4NFDI_interface.ipynb). The notebook changes the working directory into `nibelungenbruecke/scripts/digital_twin_orchestrator` and adds the repository root to `sys.path`, because the settings JSON files use paths relative to that folder:

```python
original_cwd = os.getcwd()
root_dir = os.getcwd()
orchestrator_dir = os.path.join(root_dir, 'nibelungenbruecke', 'scripts', 'digital_twin_orchestrator')
os.chdir(orchestrator_dir)
sys.path.insert(0, root_dir)

from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator import Orchestrator
```

Running the notebook from any other directory will make the model and settings paths fail to resolve. The last cell restores the original working directory.

# Notebook interfaces
Both notebooks drive the same `Orchestrator` object and differ only in which parts of the workflow they show.

## J4NFDI_interface.ipynb
The complete reference walkthrough. It covers, in order:

1. **Setup** — optional package installation, working-directory change and import of `Orchestrator`.
2. **Input parameters** — definition of the `simulation_parameters` dictionary (see [Simulation parameters](#simulation-parameters)).
3. **Initialization** — `orchestrator = Orchestrator(simulation_parameters)`.
4. **Data source authentication** — `orchestrator.set_api_key(key)`; the key is prompted for when `data_source` is `'MKP'` and left empty for `'OpenMeteo'`.
5. **Execution** — `results = orchestrator.run()`. Virtual sensors outside the mesh domain are detected and dropped before the simulation starts.
6. **Sensor plots** — `plot_real_vs_virtual_sensors_together`, `plot_all_sensors_together`, `plot_virtual_sensors` and `plot_real_vs_virtual_sensors`.
7. **Full-field response** — `plot_full_field_response`, followed by the XDMF→VTU/PVD conversion and the inline animation.
8. **Uncertainty quantification** — a second `simulation_parameters` dictionary with `uncertainty_quantification: True` and `plot_pv: False`, re-run through `orchestrator.run(simulation_parameters)`, followed by the corresponding `_with_UQ` plots.
9. **Teardown** — `os.chdir(original_cwd)`.

## 3D_View_interface.ipynb
A trimmed variant of the same flow, focused on the three-dimensional full-field response. It runs a single `3D_TransientThermal_1` simulation without UQ, shows `plot_virtual_sensors` and `plot_real_vs_virtual_sensors`, and then exports and displays the full field:

```python
from nibelungenbruecke.scripts.utilities.xdmf_to_vtu_converter import convert_xdmf_to_pvd
from nibelungenbruecke.scripts.utilities.full_field_viewer import show_full_field_widget

_pv_paths = orchestrator.get_paraview_paths()
convert_xdmf_to_pvd(
    h5_file=_pv_paths["h5_file"],
    out_dir=_pv_paths["vtu_dir"],
    pvd_file=_pv_paths["pvd_file"],
)
show_full_field_widget(_pv_paths["pvd_file"])
```

It does not include the UQ section. **Note**: the markdown of that notebook still describes an interactive viewer with a Play button and a time slider; the current implementation instead renders an animated GIF (see [Full-field response](#full-field-response)).

# The Orchestrator API
The `Orchestrator` class ([nibelungenbruecke/scripts/digital_twin_orchestrator/orchestrator.py](nibelungenbruecke/scripts/digital_twin_orchestrator/orchestrator.py)) is the central controller of the workflow. It selects the model and its settings file, initializes the `DigitalTwin` ([digital_twin.py](nibelungenbruecke/scripts/digital_twin_orchestrator/digital_twin.py)), requests the environmental data, runs the simulation and exposes the results through a set of plotters.

## Simulation parameters
The whole configuration is passed as a single dictionary:

```python
simulation_parameters = {
    'simulation_name': 'TestSimulation',
    'model': '3D_TransientThermal_1',
    'model_info': {
        'type': '3D',
        'path': ''
    },
    'data_source': 'OpenMeteo',          # or 'MKP'
    'start_time': '2023-08-01T08:00:00Z',
    'end_time': '2023-08-07T16:10:00Z',
    'time_step': '60min',
    'virtual_sensor_positions': [
        {'x': 0.0,   'y': 0.0, 'z': 0.0,   'name': 'Sensor1'},
        {'x': 1.0,   'y': 0.0, 'z': 0.0,   'name': 'Sensor2'},
        {'x': 1.78,  'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
        {'x': -1.83, 'y': 0.0, 'z': 0.0,   'name': 'Sensor4'}
    ],
    'plot_pv': True,
    'full_field_results': True,
    'uncertainty_quantification': False,
}
```

| Key | Type | Meaning |
| :-- | :--- | :------ |
| `simulation_name` | `str` | Free label for the simulation run. |
| `model` | `str` | Name of the predefined model to run (see [Available models](#available-models)). |
| `model_info.type` | `'2D'` \| `'3D'` | Geometrical dimension. Selects the settings file: `digital_twin_default_parameters.json` for 3D, `digital_twin_default_parameters_2D.json` for 2D. |
| `model_info.path` | `str` | Cross-section used by the 2D models: `'Span'` or `'Pilot'`. Empty string for 3D. |
| `data_source` | `'OpenMeteo'` \| `'MKP'` | Source of the environmental/sensor data (see [Data sources and API keys](#data-sources-and-api-keys)). |
| `start_time`, `end_time` | ISO 8601 UTC `str` | Simulation time window, e.g. `'2023-08-01T08:00:00Z'`. |
| `time_step` | pandas offset `str` | Sampling interval of the requested data and of the simulation output, e.g. `'10min'`, `'60min'`, `'240min'`. |
| `virtual_sensor_positions` | `list[dict]` | Virtual sensors, each with `x`, `y`, `z` (metres, see [Coordinate system](#coordinate-system-and-units)) and a `name`. An optional `bias` entry adds a constant offset to that sensor. |
| `plot_pv` | `bool` | Enables the ParaView/XDMF writing during the simulation. Must be `False` when `uncertainty_quantification` is `True`. |
| `full_field_results` | `bool` | Stores the full-field solution for every time step. Slower and larger output. |
| `uncertainty_quantification` | `bool` | Runs the UQ variant of the thermal model. Slower and larger output; only the `_with_UQ` plots are available afterwards. |

Sensor coordinates are checked against the mesh domain before the simulation (`query_point` in [mesh_point_detector.py](nibelungenbruecke/scripts/utilities/mesh_point_detector.py)); sensors that fall outside are removed from the run.

## Available models
The predefined models are declared in [input/settings/digital_twin_parameters.json](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json):

| `model` | Class | Description |
| :------ | :---- | :---------- |
| `3D_TransientThermal_1` | `ThermalModel` | Transient thermal simulation on the 3D mesh of the deck. |
| `2D_TransientThermal_1` | `ThermalModel` | Transient thermal simulation on a 2D cross-section (`Span` or `Pilot`). |
| `Displacement_1` | `DisplacementModel` | Linear-elastic displacement model under self weight. |
| `Displacement_2` | `DisplacementModel` | Same model with a different set of material parameters. |

When `uncertainty_quantification` is enabled for a transient thermal model, the UQ implementation in [thermal_model_uq.py](nibelungenbruecke/scripts/digital_twin_orchestrator/thermal_model_uq.py) is used instead of [thermal_model.py](nibelungenbruecke/scripts/digital_twin_orchestrator/thermal_model.py).

## Data sources and API keys
- **`'OpenMeteo'`** — open weather data retrieved through the [Open-Meteo](https://open-meteo.com/) API ([openmeteo_API.py](nibelungenbruecke/scripts/utilities/openmeteo_API.py)). No credentials are needed; pass an empty string to `set_api_key`.
- **`'MKP'`** — the private measurement database of the bridge, which also provides the real sensor measurements used in the comparison plots ([API_sensor_retrieval.py](nibelungenbruecke/scripts/utilities/API_sensor_retrieval.py)). It requires a key, prompted for in the notebook:

```python
if simulation_parameters["data_source"] == "MKP":
    key = input("\nEnter the code to connect API: ").strip()
elif simulation_parameters["data_source"] == "OpenMeteo":
    key = ""
orchestrator.set_api_key(key)
```

The plots that compare against real sensors (`plot_real_vs_virtual_sensors`, `plot_all_sensors_together`, `plot_real_vs_virtual_sensors_together`) are only meaningful with the MKP source, since only that source provides measured data.

## Methods
| Method | Purpose |
| :----- | :------ |
| `Orchestrator(simulation_parameters)` | Selects the model and settings file and initializes the digital twin and all plotters. |
| `set_api_key(key)` | Stores the credential used to retrieve the data. Must be called before `run`. |
| `run(simulation_parameters=None)` | Runs the simulation. Passing a new dictionary reconfigures the orchestrator in place — this is how the notebook switches to the UQ run without rebuilding the object. |
| `plot(plot_type)` | Produces one of the registered plots (see [Sensor plots](#sensor-plots)). |
| `get_paraview_paths()` | Returns the absolute `h5_file`, `xdmf_file`, `vtu_dir` and `pvd_file` paths of the current run. Call it after `run`. |

# Results and outputs
## Sensor plots
The available plot keys are registered in [plotters/factory.py](nibelungenbruecke/scripts/plotters/factory.py):

| Plot key | UQ counterpart | Content |
| :------- | :------------- | :------ |
| `plot_virtual_sensors` | `plot_virtual_sensors_with_UQ` | Simulated time series at each virtual sensor position. |
| `plot_real_vs_virtual_sensors` | `plot_real_vs_virtual_sensors_with_UQ` | Simulation against the corresponding real sensor measurements, one figure per sensor. |
| `plot_all_sensors_together` | `plot_all_sensors_together_with_UQ` | All real sensors of the database in a single figure. |
| `plot_real_vs_virtual_sensors_together` | `plot_real_vs_virtual_sensors_together_with_UQ` | All real sensors together with their virtual counterparts. |
| `plot_full_field_response` | *(same key)* | Reports the full-field output files of the run. |

Two rules apply:
- When `uncertainty_quantification` is `True`, only the `_with_UQ` keys are accepted; when it is `False`, only the plain keys are. `plot_full_field_response` works in both cases. Calling a non-matching key prints a message and returns without plotting.
- Every key above also exists with a `_displacement` suffix (e.g. `plot_virtual_sensors_displacement`), which plots displacements instead of temperatures. The bare keys use the temperature strategy.

## Full-field response
The full field is written by FEniCSx as an XDMF time series with an HDF5 companion file. To view it, it is first converted to a collection of VTU files referenced by a PVD manifest, and then rendered:

```python
_pv_paths = orchestrator.get_paraview_paths()
convert_xdmf_to_pvd(h5_file=_pv_paths["h5_file"], out_dir=_pv_paths["vtu_dir"], pvd_file=_pv_paths["pvd_file"])
show_full_field_widget(_pv_paths["pvd_file"])
```

- `convert_xdmf_to_pvd` ([xdmf_to_vtu_converter.py](nibelungenbruecke/scripts/utilities/xdmf_to_vtu_converter.py)) writes one base64-encoded VTU per time step plus the `.pvd` collection. The `encoding="raw"` option produces smaller files intended for the ParaView desktop application. The module can also be called from the command line.
- `show_full_field_widget` ([full_field_viewer.py](nibelungenbruecke/scripts/utilities/full_field_viewer.py)) extracts a **cross-section at mid-span (constant z)** for every time step and saves it as an **animated GIF**, which is then displayed inline in the notebook. The GIF is written to a `figures/` directory next to the PVD file. It is not an interactive 3D widget: for rotating, zooming and slicing the mesh, open the generated `.pvd` (or the original `.xdmf`) in ParaView.

## Output files
With the default settings ([digital_twin_default_parameters.json](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json)), a run writes to `use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/`:

| Path | Content |
| :--- | :------ |
| `output/paraview/Nibelungenbruecke_thermal.xdmf` / `.h5` | Full-field thermal time series. |
| `output/paraview/vtu_series/`, `output/paraview/pv_output.pvd` | VTU conversion of the above. |
| `output/paraview/figures/` | Animated GIFs produced by the viewer. |
| `output/sensors/transientthermal.json`, `transientthermal_UQ.json` | Simulated virtual-sensor time series. |
| `output/sensors/MKP_meta_output.json`, `MKP_translated.json`, `virtual_sensor_added_translated.json` | Retrieved sensor metadata and its translation to the demonstrator format. |
| `input/sensors/API_df_output.csv`, `API_meta_output.json` | Raw environmental data retrieved from the API. |

The output names and locations are configurable through `paraview_output_path`, `paraview_thermal_output_name` and the other path entries of that settings file.

# Coordinate system and units
Values are given in SI units. The coordinate system is:
- **Coordinate X**: transversal direction of the bridge (same direction as the water flow) with origin on the West shore (Worms) of the river in the middle point of the section of the deck.
- **Coordinate Y**: vertical direction of the bridge (height) with origin at the deck height at the western pilot.
- **Coordinate Z**: longitudinal direction of the bridge (direction across the river flow) with origin at the western pilot.

The same convention applies to the `virtual_sensor_positions` entries of `simulation_parameters`. Temperatures are handled in kelvin internally — the data retrieved from the APIs is given in degrees Celsius and converted on ingestion — times in seconds from the start of the simulation window, and displacements in metres.

# Extending the demonstrator
NibelungenbrueckeDemonstrator implements a set of base classes so that new implementations work seamlessly with the rest of the workflow:

- **Custom digital twin model**: derive a new class from `BaseModel` ([base_model.py](nibelungenbruecke/scripts/digital_twin_orchestrator/base_model.py)) in a new file inside [digital_twin_orchestrator](nibelungenbruecke/scripts/digital_twin_orchestrator), and register it as a new entry (`name`, `type`, `class`, `parameters`, `path`) in [digital_twin_parameters.json](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json). The entry `name` is what goes into `simulation_parameters['model']`.
- **Custom plots**: derive from `BasePlotter` ([base_plotter.py](nibelungenbruecke/scripts/plotters/base_plotter.py)) and add the class to `PlotterFactory._plotters` in [factory.py](nibelungenbruecke/scripts/plotters/factory.py). It becomes available for every registered `SensorTypeStrategy` ([sensor_strategy.py](nibelungenbruecke/scripts/plotters/sensor_strategy.py)); adding a new strategy there creates a suffixed variant of every existing plot.
- **Custom geometries**: point the `model_path` entries of the settings file to the desired `.msh` mesh. Mesh and geometry generation helpers live in [utilities/create_geometry.py](nibelungenbruecke/scripts/utilities/create_geometry.py), [create_cross_section.py](nibelungenbruecke/scripts/utilities/create_cross_section.py) and [create_mesh.py](nibelungenbruecke/scripts/utilities/create_mesh.py).
- **Custom data source**: the retrieval and translation logic is in [API_sensor_retrieval.py](nibelungenbruecke/scripts/utilities/API_sensor_retrieval.py), [openmeteo_API.py](nibelungenbruecke/scripts/utilities/openmeteo_API.py) and [sensor_translators.py](nibelungenbruecke/scripts/utilities/sensor_translators.py).
- **Custom FEM boundary conditions**: available conditions are in [utilities/boundary_conditions.py](nibelungenbruecke/scripts/utilities/boundary_conditions.py). Add new ones there and reference them from the `boundary_conditions` block of the settings JSON.
- **Custom synthetic generator model** (legacy workflow): derive from `GeneratorModel` and save it to [scripts/data_generation](nibelungenbruecke/scripts/data_generation).
- **Custom forward model** (legacy workflow): derive from probeye's `ForwardModel` and save it to [scripts/inference](nibelungenbruecke/scripts/inference).

# Legacy: doit inference workflow
Before the orchestrator was introduced, the demonstrator was run as a linear pipeline of [doit](https://pydoit.org/) tasks, controlled by [dodo.py](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/dodo.py). This pipeline is still available and is the path to use for offline Bayesian parameter identification with [probeye](https://github.com/BAMresearch/probeye). It provides the following modules:

- **Geometry and mesh creation**: from a set of parameters, it creates the geometry of the Nibelungenbrücke and meshes it.
- **Synthetic data generation**: generates a set of data at a given set of virtual sensor positions.
- **Data preprocessing**: pre-processes the data by applying the transformations indicated and adapts it to a suitable format for the DT. (WIP)
- **Run inference procedure**: applies Bayesian inference methods to obtain fitted distributions of a set of parameters based on provided data.
- **Query posterior predictive**: predicts new data points at positions where it was not available based on the previously fitted parameters.
- **Results postprocessing**: post-processes the results as requested by the user. (WIP)
- **Document generation**: generates automatically the documentation with the obtained results. (WIP)

The task manager checks whether a result is already present and avoids running any task more than once. Input files are located in `input` and the results are generated in `output` and `document`.

## Running the basic example
The basic example consists in the full workflow applied to the Nibelungenbrücke. The objective is to fit the material parameters of the bridge section given a set of displacements under its own weight simulated using a FEM model.

Navigate to the [use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete) folder and run:
```
doit
```
This will run the full workflow and output the results in `output`.

To activate or deactivate any of the tasks, toggle them at [input/settings/doit_parameters.json](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/doit_parameters.json). Note: if the results are present already, the task manager will skip that task regardless.

## Modifying the settings
To customize this workflow, modify the settings files in [input/settings](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/). The new parameter values must be changed in the JSON files, which can be modified manually or programmatically. To analyse a different set of sensors, change their definitions in [input/sensors](use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/). Virtual sensors for synthetic data generation and inference currently follow a different syntax.

## Input and output data formating
Information for the sensors contains the metadata for the set of sensors: the name and position of the sensor, the quantities it measures, the dimension of the measurements and the format in which they are provided. The data itself contains the measurements provided to or from the model following a database or dataframe structure. Values are given in SI units and follow the [coordinate system](#coordinate-system-and-units) described above.

- **Input displacement data**: provided as a `.h5` file which includes in the first level the list of sensors used to measure the displacements. In the second level, i.e. for each sensor, it indicates the data, the data series, the position of the sensor, the time values at which the data is sampled and the type of value measured. As the example collects only one measurement per sensor, the data and time series have only one entry each. Input measurements (for example, loads) must be located in a different file than output ones (for example, displacements). Example:

| DisplacementSensor0 |                    |    Units    |
| :-----------------: | :----------------: | :---------: |
|        Data         |  [y_1, y_2, y_3]   | meters [m]  |
|        Time         |        1.0         | seconds [s] |
|      Position       | [ 0.0 , 0.0, 50.0] | meters [m]  |
|        Type         |  "Displacements"   |      -      |
|     Error model     |      Gaussian      |      -      |
|      Error std      |        0.0         | meters [m]  |

- **Information on the output sensors**: indicates to the demonstrator which information it must produce and where. It is currently given in the sensors' `.json` files with the same metadata.

- **Output posterior predictive data**: the posterior predictive queries provide the same information and format as the input displacement data, but add statistical information. These statistical values (max, min, mean, std) refer to the specific set of random samples generated for the posterior predictive. The chosen samples are included in the output structure. Example:

|  disp_span_new_1   |                            |    Units    |
| :----------------: | :------------------------: | :---------: |
|        Data        |   [y_1, y_2, y_3] x 100    | meters [m]  |
|        Time        |      *Not available*       | seconds [s] |
|      Position      |     [ 0.0 , 0.0, 25.0]     | meters [m]  |
|        Max         |  [ max_1 , max_2, max_3]   | meters [m]  |
|        Mean        | [ mean_1 , mean_2, mean_3] | meters [m]  |
|        Min         |  [ min_1 , min_2, min_3]   |  meters[m]  |
| Standard deviation |  [ std_1 , std_2, std_3]   |  meters[m]  |
|        Type        |      "Displacements"       |      -      |

# Integration in a larger Digital Twin
The NibelungenbrueckeDemonstrator is designed to work as an independent module with respect to its integration in a larger Digital Twin. The `Orchestrator` is the callable interface for that integration: an external system builds a `simulation_parameters` dictionary, provides the credentials for the data source and calls `run`, retrieving the results either as the returned time series or from the output files described in [Output files](#output-files).

The module needs access to the sensor measurements stored in the Digital Twin's database and to their metadata, and it must be able to upload new predictions back. These can be in the form of raw data (binary/serializable), or as figures and graphs upon request.

It is initially set up with a predefined model and settings, that can potentially be updated at run time — `run` accepts a new parameter dictionary and reconfigures the models accordingly. It is intended that the model can be updated automatically or on demand from a set of suggestions.

In its current state, the demonstrator provides temperature and displacement information at virtual sensor positions, plus the full-field response. This can be extended to evaluate the predictions automatically, obtaining key performance indicators (KPIs) or providing further insight on the state of the bridge, implemented as post-processing tasks or as external modules.

# TO-DO
- Implement CI/CD
- Implement tests
- Implement automatic document generation
- Comprehensive documentation
- Code formating
- Interactive full-field viewer in the notebook interface
