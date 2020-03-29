from functools import wraps
from typing import Type, TypeVar, Callable
from unittest import mock

import appdaemon.plugins.hass.hassapi as hass
import pytest
from appdaemon.logging import Logging

from ..hass_driver import HassDriver


@pytest.fixture()
def hass_driver() -> HassDriver:
    """
    Pytest fixture for `appdaemon_testing.HassDriver`.

    This fixture takes care of ensuring AppDaemon base class methods are patched.
    """
    hass_driver = HassDriver()
    hass_driver.inject_mocks()
    return hass_driver


T = TypeVar("T", bound=hass.Hass)


def automation_fixture(App: Type[T], args=None, initialize=True):
    """
    Configures a pytest fixture for the given AppDaemon automation.

    Parameters:
        App: The AppDaemon application to create the fixture for
        args: arguments that should be provided to the app when it is
              instantiated (`self.args`)
        initialize: Whether `app.initialize()` should be called.
    """

    def decorator(fn) -> Callable[..., T]:
        @pytest.fixture()
        @wraps(fn)
        def inner(*_args, **_kwargs) -> T:
            ad = mock.Mock()
            logging_impl = mock.Mock()
            logging_impl.log_levels = Logging.log_levels
            app = App(ad, App.__name__, logging_impl, args or {}, {}, {}, {})
            if initialize:
                app.initialize()
            fn(*_args, **_kwargs)
            return app

        return inner

    return decorator


__all__ = ["automation_fixture", "hass_driver"]
