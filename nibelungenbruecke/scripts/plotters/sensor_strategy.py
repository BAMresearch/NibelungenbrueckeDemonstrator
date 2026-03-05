from abc import ABC, abstractmethod


class SensorTypeStrategy(ABC):
    """Abstract strategy that encapsulates sensor-type-specific plot configuration."""

    @property
    @abstractmethod
    def sensor_type(self) -> str:
        """Canonical name used to match 'sensor_type' entries in virtual_sensor_positions."""
        ...

    @property
    @abstractmethod
    def ylabel(self) -> str:
        """Y-axis label for all plots produced with this strategy."""
        ...

    @property
    @abstractmethod
    def unit(self) -> str:
        """Physical unit string (e.g. 'K', 'm')."""
        ...

    @property
    @abstractmethod
    def title_prefix(self) -> str:
        """Short human-readable prefix used in plot titles."""
        ...


class TemperatureStrategy(SensorTypeStrategy):
    """Strategy for temperature sensors (default)."""

    sensor_type = "temperature"
    ylabel = "Temperature (K)"
    unit = "K"
    title_prefix = "Temperature"


class DisplacementStrategy(SensorTypeStrategy):
    """Strategy for displacement sensors."""

    sensor_type = "displacement"
    ylabel = "Displacement (m)"
    unit = "m"
    title_prefix = "Displacement"


# Registry kept in sync with concrete strategies for easy look-up.
STRATEGY_REGISTRY: dict[str, SensorTypeStrategy] = {
    "temperature": TemperatureStrategy(),
    "displacement": DisplacementStrategy(),
}


def get_strategy(sensor_type: str) -> SensorTypeStrategy:
    """Return the strategy instance for *sensor_type* (case-insensitive).

    Falls back to :class:`TemperatureStrategy` when the type is unknown.
    """
    return STRATEGY_REGISTRY.get(sensor_type.lower(), TemperatureStrategy())
