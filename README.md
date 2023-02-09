## TO-DO
- Implement CI/CD
- Implement tests
- Implement automatic document generation
- Minimal environment dependencies
- Comprehensive documentation
- Code formating

__________________
## Table of Contents

- [Introduction](#introduction)
- [Bridge description](#bridge-description)
  - [Location](#location)
  - [Structure](#structure)
  - [Materials](#materials)
- [Code dependencies](#code-dependencies)
- [Installation and use](#installation-and-use)
  - [Installation](#installation)
  - [Use](#use)
    - [Running the basic example](#running-the-basic-example)
    - [Modifying the settings](#modifying-the-settings)
    - [Input and Output data formating](#input-and-output-data-formating)
    - [Adding custom functionalities](#adding-custom-functionalities)
- [Expected results](#expected-results)
- [Integration in a larger Digital Twin](#integration-in-a-larger-digital-twin)

# Introduction
The goal of **NibelungenbrueckeDemonstrator** is to provide a representative and repeatable workflow for the implementation of a stochastic [Digital Twin (DT)](https://en.wikipedia.org/wiki/Digital_twin) of the [Nibelungenbrücke in Worms (Germany)](https://de.wikipedia.org/wiki/Nibelungenbr%C3%BCcke_Worms). This repository has been developed by [_Bundesanstalt für Materialforschung und -prüfung (BAM)_](https://www.bam.de) in the context of the project "Data driven model adaptation for identifying stochastic digital twins of bridges", englobed in the funding initiative SPP 2388/1 100plus of the German Research Foundation (DFG). 

Nevertheless, due to its modular structure and user-oriented approach, this demonstrator can be used as the basis for implementing the workflow of any digital twin using a [Bayesian framework](https://en.wikipedia.org/wiki/Bayesian_inference). This repository abides by the principles of [FAIR](https://www.go-fair.org/fair-principles/) (Findable, Accessible, Interoperable and Reusable) scientific software.
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
# Code dependencies
The following packages are required:
- [doit](https://pydoit.org/)
- [fenics-dolfinx](https://github.com/FEniCS/dolfinx)
- [gmsh](https://gmsh.info/)
- [h5py](https://www.h5py.org/)
- [probeye](https://github.com/BAMresearch/probeye)

For visualization, [paraview](https://www.paraview.org/) is recommended. These packages may require their own dependencies such as numpy, scipy, pandas, etc.

Alternatively, import the conda environment as
```
conda env create -n ENVNAME --file nibelungenbruecke.yml
```
*INCLUDE MINIMUM VERSIONS*

# Installation and use
## Installation
From the root of the cloned repository, install the folder as a package using pip:
```
pip install .
```
Now the contents in `nibelungenbruecke` are available for their use in any Python script calling `import nibelungenbruecke`.

## Use
The NibelungenbrückeDemonstrator provides the following modules:
- **Geometry and mesh creation**: From a set of parameters, it creates the geometry of the Nibelungenbrücke and meshes it.
- **Synthetic data generation**: Generates a set of data a a given set of virtual sensor positions.
- **Data preprocessing**: Pre-processes the data by applying the transformations indicated and adapts it to a suitable format for the DT. (WIP)
- **Run inference procedure**: Applies Bayesian inference methods to obtain fitted distributions of a set of parameters based on provided data.
- **Query posterior predictive**: Predicts new data points at positions where it was not available based on the previously fitted parameters.
- **Results postprocessing**: Post-processes the results as requested by the user. (WIP)
- **Document generation**: Generates automatically the documentation with the obtained results. (WIP)

The demonstrator is implemented as a set of [doit](https://pydoit.org/) tasks run after each other. This workflow allows checking if one result is already present or not, and avoid running any task more than once. The script that controls this is [dodo.py](dodo.py). Input files must be located in the folder `input` and the results will be generated in `output` and `document`.
### Running the basic example
The basic example consists in the full workflow applied to the Nibelungenbrücke. It will be used the basic example on how to run and implement the necessary tasks. In this case, the objective is to fit the material parameters of the bridge section given a set of displacements under its own weight simulated using a FEM model.

To run the example from a clean installation, navigate to the `use_cases/nibelungenbruecke_demonstrator` folder and run the command:
```
doit
```
This will run the full workflow and output results for the basic example in the results folder from `output`.

To activate or deactivate any of the tasks, toggle them at [input/settings/doit_parameters.json](use_cases/nibelungenbruecke_demonstrator/input/settings/doit_parameters.json). Note: If the results are present already, the task manager will skip that task regardless.
### Modifying the settings
To customize the demonstrator, it suffices with modifying the settings files in [input/settings](use_cases/nibelungenbruecke_demonstrator/input/settings/) with the desired ones. They new values parameters must be changed in the JSON files, which can be modified manually or programatically. Notice that these modifications impact only to the methods implemented in this repository.

Another probable requirement would be the analysis of a different set of sensors. To modify their characteristics and locations, change them in their definitions from [input/sensors](use_cases/nibelungenbruecke_demonstrator/input/sensors/). Virtual sensors for synthetic data generation and inference follow currently a different sintaxis.

### Input and Output data formating
Properly retrieving and providing data is key for the good performance of the demonstrator. We can differentiate the information provided about the sensors and the data itself. Information for the sensors contains the metadata for the set of sensors. This includes the name and position of the sensor, as well as what quantities it is measuring, the dimension of the measurements and the format in which they are provided. Alternatively, the data itself contains the measurements provided to or from the model following a database or dataframe structure. As a general reference, the values are given with units in the international system (SI units).
The coordinate system follows:
- **Coordinate X**: transversal direction of the bridge (same direction as the water flow) with origin on the West shore (Worms) of the river in the middle point of the section of the deck.
- **Coordinate Y**: vertical direction of the bridge (height) with origin at the deck height at the western pilot.
- **Coordinate Z**: longitudinal direction of the bridge (direction accross the river flow) with origin at the western pilot
  
Currently, the following sensors and structures are defined for the demonstrator example:
- **Input displacement data**: It is provided as a `.h5` file wich includes in the first level the list of sensors used to measure the displacements. In the second level, i.e. for each sensor, we indicate the data, the data series, the position of the sensor, the time values at which the data is sampled and the type of value that we are measuring. As in the example we collect only one measurement per sensor, the data and time series will have only one entry each. Input measurements (for example, loads) must be located in a different file than output ones (for example, displacements). Example:
  
| DisplacementSensor0 |                    |    Units    |
| :-----------------: | :----------------: | :---------: |
|        Data         |  [y_1, y_2, y_3]   | meters [m]  |
|        Time         |        1.0         | seconds [s] |
|      Position       | [ 0.0 , 0.0, 50.0] | meters [m]  |
|        Type         |  "Displacements"   |      -      |
|     Error model     |      Gaussian      |      -      |
|      Error std      |        0.0         | meters [m]  |

- **Information on the output sensors**: This information is necessary to indicate the demonstrator which information it must produce and where. It is currently indicated in the sensor's `.json` files with the same metadata. *It would be possible to implement a function that retrieves the metadata information to another format*.

- **Output posterior predictive data**: The posterior predictive queries provide the same information and format as in **Input displacement** but adds statistical information. These statistical values (max, min, mean, std) refer to the specific set of random samples generated for the posterior predictive. Additionally, the posterior data is generated from a sampling procedure and the chosen samples are included in the output structure. Example:
  
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

**Note**: It is possible to implement a function as a pre-processing step that queries a database and transform the data from the native format to the format required by NibelungenbrueckeDemonstrator. Analogously, a post-processing function that transforms back the data to the required format and uploads them to a database is equally possible. Currently that is substituted by paths directions indicated in the `.json` settings' files.
### Adding custom functionalities
To add easily new functionalities, NibelungenBruecke implements a set of base classes that allow for the new implementations to work seamlesly with the rest of the demonstrator. Current available options are:
- **Custom geometries**: simply deactivate the "generate model task" and indicate the path to the desired mesh
- **Custom data input**: analogously to custom geometries, deactivate the corresponding task and indicate the path to data accordingly. The data format and structure must be compatible with the inference model.
- **Custom synthetic generator model**: Derive a new class from `GeneratorModel` in a new file and save it to [nibelungenbruecke/scripts/data_generation](nibelungenbruecke/scripts/data_generation). Modify the settings' JSON file to point to this model as the generator.
- **Custom forward model**: Derive a new class from probeye's `ForwardModel` in a new file and save it to [nibelungenbruecke/scripts/inference](nibelungenbruecke/scripts/inference). Modify the settings' JSON file to point to this model as the generator.
- **Custom FEM boundary conditions**: The available boundary conditions are located at [nibelungenbruecke/scripts/utilities/boundary_conditions.py](nibelungenbruecke/scripts/utilities/boundary_conditions.py). Add new ones to the file and call them from the definition in the settings JSON file.
  
# Expected results
WIP
# Integration in a larger Digital Twin
The NibelungenBruecke Demonstrator is designed to work as an independent module with respect to its integration in a larger Digital Twin. The module is conceived as a group of subroutines that can be called regularly, either to perform predictions or to refit the model. There is a need for internal data storage for the current state, or access to a database where it can be stored. The NibelungenBrueckeDemonstrator module needs access to the sensor measurements stored in the Digital Twin's database and to its metadata.  Likewise, it must be able to upload new predictions to the database. These can be in the form of raw data (binary/serializable), or as figures and graphs upon request. 

It is initially set-up with a predefined model and settings, that can potentially be updated on the run. It is intended that this model can be updated automatically or on demand from a set of suggestions. Therefore, the end user must be able to call a function to trigger such an update, or to set it to be made automatically. 

In its current state, the demonstrator provides displacements information at virtual sensor positions. However, this can be easily extended to perform automatically evaluations on the predictions, obtaining key performance indicators (KPIs) or providing further insight on the state of the bridge to be provided to the end user. This can be easily implemented as post-processing tasks or as external modules.


