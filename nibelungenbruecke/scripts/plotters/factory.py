from nibelungenbruecke.scripts.plotters.base_plotter import *
from nibelungenbruecke.scripts.plotters.sensor_strategy import (
    SensorTypeStrategy,
    TemperatureStrategy,
    DisplacementStrategy,
    get_strategy,
)


class PlotterFactory:
    """Factory to create plotter instances based on the model and plotter class.

    Each registered *plot_type* key can be used with any :class:`SensorTypeStrategy`.
    By default all plotters are created with :class:`TemperatureStrategy`.

    A displacement variant of every plot type is also available by appending the
    ``_displacement`` suffix (e.g. ``"plot_virtual_sensors_displacement"``).  The
    orchestrator registers both sets automatically via :meth:`create_all_plotters`.
    """

    _plotters = {
        "plot_real_vs_virtual_sensors_together": RealvsVirtualAllTogether,
        "plot_real_vs_virtual_sensors_together_with_UQ": RealvsVirtualAllTogetherUQ,
        "plot_all_sensors_together": AllSensorsTogetherPlotter,
        "plot_all_sensors_together_with_UQ": AllSensorsTogetherPlotterUQ,
        "plot_full_field_response": FullFieldResponsePlotter,
        "plot_real_vs_virtual_sensors_with_UQ": RealVsVirtualPlotterUQ,
        "plot_real_vs_virtual_sensors": RealVsVirtualPlotter,
        "plot_virtual_sensors": VirtualSensorPlotter,
        "plot_virtual_sensors_with_UQ": VirtualSensorPlotterUQ,
    }

    @staticmethod
    def create_plotter(
        plot_type: str,
        problem=None,
        simulation_parameters=None,
        default_parameters=None,
        strategy: SensorTypeStrategy = None,
    ) -> BasePlotter:
        """Return a single plotter instance for *plot_type*.

        Parameters
        ----------
        strategy:
            Sensor-type strategy to inject.  Defaults to
            :class:`TemperatureStrategy` when *None*.
        """
        plotter_class = PlotterFactory._plotters.get(plot_type.lower())
        if not plotter_class:
            raise ValueError(f"Unknown plot type: {plot_type}")
        return plotter_class(
            problem=problem,
            simulation_parameters=simulation_parameters,
            default_parameters=default_parameters,
            strategy=strategy,
        )

    @staticmethod
    def create_all_plotters(
        problem=None,
        simulation_parameters=None,
        default_parameters=None,
        strategy: SensorTypeStrategy = None,
    ) -> dict:
        """Return a dict of ``{plot_type: plotter_instance}`` for *all* registered types.

        Parameters
        ----------
        strategy:
            Strategy to inject into every plotter.  Defaults to
            :class:`TemperatureStrategy` when *None*.
        """
        _strategy = strategy if strategy is not None else TemperatureStrategy()
        return {
            ptype: cls(
                problem=problem,
                simulation_parameters=simulation_parameters,
                default_parameters=default_parameters,
                strategy=_strategy,
            )
            for ptype, cls in PlotterFactory._plotters.items()
        }

    @staticmethod
    def create_all_plotters_for_strategies(
        problem=None,
        simulation_parameters=None,
        default_parameters=None,
        strategies: list[SensorTypeStrategy] = None,
    ) -> dict:
        """Return plotters for *multiple* strategies in a single dict.

        Temperature plotters are registered under their bare names (e.g.
        ``"plot_virtual_sensors"``); every other strategy uses a suffixed key
        (e.g. ``"plot_virtual_sensors_displacement"``).

        Parameters
        ----------
        strategies:
            List of strategy instances to create plotters for.  Defaults to
            ``[TemperatureStrategy(), DisplacementStrategy()]``.
        """
        if strategies is None:
            strategies = [TemperatureStrategy(), DisplacementStrategy()]

        combined: dict = {}
        for strat in strategies:
            suffix = "" if isinstance(strat, TemperatureStrategy) else f"_{strat.sensor_type}"
            for ptype, cls in PlotterFactory._plotters.items():
                key = ptype if not suffix else f"{ptype}{suffix}"
                combined[key] = cls(
                    problem=problem,
                    simulation_parameters=simulation_parameters,
                    default_parameters=default_parameters,
                    strategy=strat,
                )
        return combined
    
