import contextlib
import logging
import unittest.mock as mock
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import Dict, Any, List, Callable, Union, Optional

import appdaemon.plugins.hass.hassapi as hass

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class StateSpy:
    callback: Callable
    attribute: Optional[str]
    new: Optional[str]
    old: Optional[str]
    kwargs: Any


class HassDriver:
    def __init__(self):
        self._mocks = dict(
            call_service=mock.Mock(),
            cancel_timer=mock.Mock(),
            get_state=mock.Mock(side_effect=self._se_get_state),
            # TODO(NW): Implement side-effect for listen_event
            listen_event=mock.Mock(),
            fire_event=mock.Mock(),
            listen_state=mock.Mock(side_effect=self._se_listen_state),
            notify=mock.Mock(),
            run_at=mock.Mock(),
            run_at_sunrise=mock.Mock(),
            run_at_sunset=mock.Mock(),
            run_daily=mock.Mock(),
            run_every=mock.Mock(),
            run_hourly=mock.Mock(),
            run_in=mock.Mock(),
            run_minutely=mock.Mock(),
            set_state=mock.Mock(),
            time=mock.Mock(),
            turn_off=mock.Mock(),
            turn_on=mock.Mock(),
        )

        self._setup_active = False
        self._states: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"state": None})
        self._state_spys: Dict[Union[str, None], List[StateSpy]] = defaultdict(
            lambda: []
        )

    def get_mock(self, meth: str) -> mock.Mock:
        return self._mocks[meth]

    def inject_mocks(self):
        for meth_name, impl in self._mocks.items():
            if getattr(hass.Hass, meth_name) is None:
                raise AssertionError("Attempt to mock non existing method: ", meth_name)
            _LOGGER.debug("Patching hass.Hass.%s", meth_name)
            setattr(hass.Hass, meth_name, impl)

    @contextlib.contextmanager
    def setup(self):
        self._setup_active = True
        yield None
        self._setup_active = False

    def set_state(
        self, entity, state, *, attribute_name="state", previous=None, trigger=None
    ):
        if trigger is None:
            # Avoid triggering state changes during state setup phase
            trigger = not self._setup_active

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
                domain, entity = s_eid.split(".")
                if domain == entity_id:
                    matched_states[s_eid] = state

        # With matched states, map the provided attribute (if applicable)
        if attribute != "all":
            matched_states = {
                eid: state.get(attribute) for eid, state in matched_states.items()
            }

        if default is not None:
            matched_states = {
                eid: state or default for eid, state in matched_states.items()
            }

        if fully_qualified:
            return matched_states[entity_id]
        else:
            return matched_states

    def _se_listen_state(
        self, callback, entity=None, attribute=None, new=None, old=None, **kwargs
    ):
        spy = StateSpy(
            callback=callback,
            attribute=attribute or "state",
            new=new,
            old=old,
            kwargs=kwargs,
        )
        self._state_spys[entity].append(spy)
