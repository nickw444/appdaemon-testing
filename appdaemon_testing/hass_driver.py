import contextlib
import logging
import unittest.mock as mock
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import appdaemon.plugins.hass.hassapi as hass

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class StateSpy:
    callback: Callable
    attribute: Optional[str]
    new: Optional[str]
    old: Optional[str]
    kwargs: Any


@dataclass(frozen=True)
class EventSpy:
    callback: Callable
    event_name: str


class HassDriver:
    def __init__(self):
        self._mocks = dict(
            log=mock.Mock(),
            error=mock.Mock(),
            call_service=mock.Mock(),
            cancel_listen_state=mock.Mock(side_effect=self._se_cancel_listen_state),
            cancel_timer=mock.Mock(),
            get_state=mock.Mock(side_effect=self._se_get_state),
            listen_event=mock.Mock(side_effect=self._se_listen_event),
            fire_event=mock.Mock(side_effect=self._se_fire_event),
            listen_state=mock.Mock(side_effect=self._se_listen_state),
            notify=mock.Mock(),
            run_at=mock.Mock(),
            run_at_sunrise=mock.Mock(),
            run_at_sunset=mock.Mock(),
            run_daily=mock.Mock(),
            run_every=mock.Mock(),
            run_hourly=mock.Mock(),
            run_in=mock.Mock(side_effect=self._se_run_in),
            run_minutely=mock.Mock(),
            set_state=mock.Mock(side_effect=self._se_set_state),
            time=mock.Mock(),
            turn_off=mock.Mock(),
            turn_on=mock.Mock(),
        )

        self._setup_active = False
        self._states: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"state": None})
        self._events: Dict[str, Any] = defaultdict(lambda: [])
        self._state_spys: Dict[Union[str, None], List[StateSpy]] = defaultdict(lambda: [])
        self._event_spys: Dict[str, EventSpy] = defaultdict(lambda: [])
        self._run_in_simulations = []
        self._clock_time = 0  # Simulated time in seconds

    def get_mock(self, meth: str) -> mock.Mock:
        """
        Returns the mock associated with the provided AppDaemon method

        Parameters:
            meth: The method to retreive the mock implementation for
        """
        return self._mocks[meth]

    def inject_mocks(self) -> None:
        """
        Monkey-patch the AppDaemon hassapi.Hass base-class methods with mock
        implementations.
        """
        for meth_name, impl in self._mocks.items():
            if getattr(hass.Hass, meth_name) is None:
                raise AssertionError("Attempt to mock non existing method: ", meth_name)
            _LOGGER.debug("Patching hass.Hass.%s", meth_name)
            setattr(hass.Hass, meth_name, impl)

    @contextlib.contextmanager
    def setup(self):
        """
        A context manager to indicate that execution is taking place during a
        "setup" phase.

        This context manager can be used to configure/set up any existing states
        that might be required to run the test. State changes during execution within
        this context manager will cause `listen_state` handlers to not be called.

        Example:

        ```py
        def test_my_app(hass_driver, my_app: MyApp):
            with hass_driver.setup():
                # Any registered listen_state handlers will not be called
                hass_driver.set_state("binary_sensor.motion_detected", "off")

            # Respective listen_state handlers will be called
            hass_driver.set_state("binary_sensor.motion_detected", "on")
            ...
        ```
        """
        self._setup_active = True
        yield None
        self._setup_active = False

    def _se_set_state(self, entity_id: str, state, attribute_name="state", **kwargs: Optional[Any]):
        state_entry = self._states[entity_id]

        # Update the state entry
        state_entry[attribute_name] = state

    def set_state(self, entity, state, *, attribute_name="state", previous=None, trigger=None) -> None:
        """
        Update/set state of an entity.

        State changes will cause listeners (via listen_state) to be called on
        their respective state changes.

        Parameters:
            entity: The entity to update
            state: The state value to set
            attribute_name: The attribute to set
            previous: Forced previous value
            trigger: Whether this change should trigger registered listeners
                    (via listen_state)
        """
        if trigger is None:
            # Avoid triggering state changes during state setup phase
            trigger = not self._setup_active

        # _se_set_state(entity_id, attribute)
        domain, _ = entity.split(".")
        state_entry = self._states[entity]
        prev_state = copy(state_entry)
        old_value = previous or prev_state.get(attribute_name)
        new_value = state

        if old_value == new_value:
            return

        # Update the state entry
        state_entry[attribute_name] = new_value

        if not trigger:
            return

        # Notify subscribers of the change
        for spy in self._state_spys[domain] + self._state_spys[entity]:
            sat_attr = spy.attribute == attribute_name or spy.attribute == "all"
            sat_new = spy.new is None or spy.new == new_value
            sat_old = spy.old is None or spy.old == old_value

            param_old = prev_state if spy.attribute == "all" else old_value
            param_new = copy(state_entry) if spy.attribute == "all" else new_value
            param_attribute = None if spy.attribute == "all" else attribute_name

            if all([sat_old, sat_new, sat_attr]):
                spy.callback(entity, param_attribute, param_old, param_new, spy.kwargs)

    def _se_get_state(self, entity_id=None, attribute="state", default=None, **kwargs):
        _LOGGER.debug("Getting state for entity: %s", entity_id)

        fully_qualified = "." in entity_id
        matched_states = {}
        if fully_qualified:
            matched_states[entity_id] = self._states[entity_id]
        else:
            for s_eid, state in self._states.items():
                domain, _ = s_eid.split(".")
                if domain == entity_id:
                    matched_states[s_eid] = state

        # With matched states, map the provided attribute (if applicable)
        if attribute != "all":
            matched_states = {eid: state.get(attribute) for eid, state in matched_states.items()}

        if default is not None:
            matched_states = {eid: state or default for eid, state in matched_states.items()}

        if fully_qualified:
            return matched_states[entity_id]
        else:
            return matched_states

    def get_number_of_state_callbacks(self, entity):
        if entity in self._state_spys.keys():
            return len(self._state_spys.get(entity))
        return 0

    def _se_listen_state(self, callback, entity=None, attribute=None, new=None, old=None, **kwargs) -> StateSpy:
        spy = StateSpy(
            callback=callback,
            attribute=attribute or "state",
            new=new,
            old=old,
            kwargs=kwargs,
        )
        # WARNING: This works only if function setting callback is called after setup.
        # It may be required to defer initialize by setting initialize to False in fixture definition
        # and calling <app>.initialize() after setup
        self._state_spys[entity].append(spy)
        if "immediate" in spy.kwargs and spy.kwargs["immediate"] is True:
            state = self._states[entity][spy.attribute]
            if (spy.new is None) or (spy.new == state):
                spy.callback(entity=entity, attribute="state", new=state, old=old, kwargs=spy.kwargs)
        return spy

    def _se_cancel_listen_state(self, handle):
        for key, states in self._state_spys.items():
            for value in states:
                if value == handle:
                    states.remove(value)
                    if not states:
                        del self._state_spys[key]
                    return

    def _se_listen_event(self, callback, event_name) -> EventSpy:
        spy = EventSpy(
            callback=callback,
            event_name=event_name,
        )
        self._event_spys[event_name].append(spy)
        return spy

    def _se_fire_event(self, event_name, **kwargs):
        if event_name in self._event_spys:
            spy = self._event_spys[event_name][0]
            spy.callback(event_name=event_name, data=kwargs, kwargs=kwargs)

    def set_clock_time(self, time_in_seconds):
        """
        Set the simulated clock time.
        """
        self._clock_time = time_in_seconds

    def _se_run_in(self, callback, delay, **kwargs):
        """
        Simulate an AppDaemon run_in call.
        return handle
        """
        run_time = self._clock_time + delay
        self._run_in_simulations.append({"callback": callback, "run_time": run_time, "kwargs": kwargs})
        return callback

    def get_run_in_simulations(self):
        """
        Get the list of simulated run_in calls.
        """
        return self._run_in_simulations

    def advance_time(self, seconds):
        """
        Advance the simulated clock time by the specified number of seconds.
        """
        self._clock_time += seconds

        # Check for any run_in calls that should be triggered
        for sim in self._run_in_simulations:
            if sim["run_time"] <= self._clock_time:
                callback = sim["callback"]
                kwargs = sim["kwargs"]
                if callable(callback):
                    callback(None, **kwargs)  # Call the callback immediately

                # Remove the triggered run_in simulation
                self._run_in_simulations.remove(sim)
