"""eWaterCycle wrapper for the HBV model."""
import json
import os.path
import numpy
import warnings
from collections.abc import ItemsView
from pathlib import Path
from typing import Any, Type

from ewatercycle.util import get_time
from ewatercycle_lorenz.forcing import LorenzForcing # Use custom forcing instead
from ewatercycle.base.model import ContainerizedModel, eWaterCycleModel
from ewatercycle.container import ContainerImage

LORENZ_PARAMS = ("J")
LORENZ_STATES = ("startState")
class LorenzMethods(eWaterCycleModel):
    """
    The eWatercycle HBV model.
    

    """
    forcing: LorenzForcing  # The model requires forcing.
    parameter_set: None  # The model has no parameter set.

    _config: dict = {
        "F": 1,
        "dt": 1,
        "J": 10,
        "start_state": [0,0,0]
                    }

    def _make_cfg_file(self, **kwargs) -> Path:
        """Write model configuration file."""

        self._config["F"] = self.forcing.F
        self._config["dt"] = self.forcing.dt
        self._config["start_time"] = 0
        # relative
        time_delta = get_time(self.forcing.end_time) - get_time(self.forcing.start_time)
        self._config["end_time"] = time_delta.days + time_delta.seconds / (3600 * 24)

        for kwarg in kwargs:  # Write any kwargs to the config. - doesn't overwrite config?
            self._config[kwarg] = kwargs[kwarg]

        config_file = self._cfg_dir / "lorenz_config.json"

        with config_file.open(mode="w") as f:
            f.write(json.dumps(self._config, indent=4))


        return config_file

    @property
    def parameters(self) -> ItemsView[str, Any]:
        """List the (initial!) parameters for this model.

        Exposed Lorenz parameters:
            J: dimension of model

        """
        pars: dict[str, Any] = dict(zip(LORENZ_PARAMS, [self._config[param] for param in LORENZ_PARAMS]))
        return pars.items()

    @property
    def states(self) -> ItemsView[str, Any]:
        """List the (initial!) states for this model.

        Exposed Lorenz states:
            startState: starting vector

        """
        pars: dict[str, Any] = dict(zip(LORENZ_STATES, [self._config[state] for state in LORENZ_STATES]))
        return pars.items()


    def finalize(self) -> None:
        """Perform tear-down tasks for the model.

        After finalization, the model should not be used anymore.

        ADDED: Remove created config files, especially useful for DA models
        """

        # remove bmi
        self._bmi.finalize()
        del self._bmi

        try:
            # remove config file
            config_file = self._cfg_dir / "Lorenz_config.json"
            config_file.unlink()
        except FileNotFoundError:
            warnings.warn(message=f'Config not found at {config_file}, removed by user?',category=UserWarning)

        try:
            # once empty, remove it
            self._cfg_dir.rmdir()
        except FileNotFoundError:
            warnings.warn(message=f'Config folder not found at {self._cfg_dir.rmdir()}',category=UserWarning)

class Lorenz(ContainerizedModel, LorenzMethods):
    """The Lorenz eWaterCycle model, with the Container Registry docker image."""
    bmi_image: ContainerImage = ContainerImage(
        "ghcr.io/daafip/lorenz-grpc4bmi:v.0.0.5"
    )
