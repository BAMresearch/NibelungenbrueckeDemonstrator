from nibelungenbruecke.scripts.plotters.base_plotter import *

class PlotterFactory:
    """Factory to create plotter instances based on the model and plotter class"""
    
    _plotters = {
        "plot_real_vs_virtual_sensors_together": RealvsVirtualAllTogether,
        "plot_all_sensors_together": AllSensorsTogetherPlotter,
        "plot_all_sensors_together_with_UQ": AllSensorsTogetherPlotterUQ,
        "plot_full_field_response": FullFieldPlotter,
        "plot_real_vs_virtual_sensors_with_UQ": RealVsVirtualPlotterUQ,
        "plot_real_vs_virtual_sensors": RealVsVirtualPlotter,
        "plot_virtual_sensors": VirtualSensorPlotter,
        "plot_virtual_sensors_with_UQ":VirtualSensorPlotterUQ,
        }


    @staticmethod 
    def create_plotter(plot_type: str, problem=None, simulation_parameters=None, default_parameters=None) -> BasePlotter:
        plotter_class = PlotterFactory._plotters.get(plot_type.lower())
        if not plotter_class:
            raise ValueError(f"Unknown plot type: {plot_type}")
        return plotter_class(problem=problem, simulation_parameters=simulation_parameters,
                       default_parameters=default_parameters
                       )
        
        
    @staticmethod 
    def create_all_plotters(problem=None, simulation_parameters=None, default_parameters=None) -> dict:
        return {
            ptype: cls(problem=problem, simulation_parameters=simulation_parameters,
                           default_parameters=default_parameters
                           ) for ptype, cls in PlotterFactory._plotters.items()
                }
    
