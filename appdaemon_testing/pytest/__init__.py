from functools import wraps
from typing import Type, TypeVar, Callable
from unittest import mock

import appdaemon.plugins.hass.hassapi as hass
import pytest

from ..hass_driver import HassDriver


@pytest.fixture()
def hass_driver() -> HassDriver:
    hass_driver = HassDriver()
    hass_driver.inject_mocks()
    return hass_driver


T = TypeVar("T", bound=hass.Hass)


def automation_fixture(App: Type[T], args=None, initialize=True):
    def decorator(fn) -> Callable[..., T]:
        @pytest.fixture()
        @wraps(fn)
        def inner(*_args, **_kwargs) -> T:
            ad = mock.Mock()
            logging = mock.Mock()
            app = App(ad, App.__name__, logging, args or {}, {}, {}, {})
            if initialize:
                app.initialize()
            fn(*_args, **_kwargs)
            return app

        return inner

    return decorator


__all__ = ['automation_fixture', 'hass_driver']
