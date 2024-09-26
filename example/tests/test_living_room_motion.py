from unittest import mock

from apps.living_room_motion import LivingRoomMotion

from appdaemon_testing.pytest import (  # noqa F401; pylint: disable=W0611
    automation_fixture,
    hass_driver,
)


def test_callbacks_are_registered(
    hass_driver,  # noqa F811
    living_room_motion: LivingRoomMotion,  # noqa F811
):  # pylint: disable=W0621
    listen_state = hass_driver.get_mock("listen_state")
    listen_state.assert_called_once_with(
        living_room_motion.on_motion_detected, "binary_sensor.motion_detected"
    )


def test_lights_are_turned_on_when_motion_detected(
    hass_driver,  # noqa F811
    living_room_motion: LivingRoomMotion,  # noqa F811
):  # pylint: disable=W0621
    with hass_driver.setup():
        hass_driver.set_state("binary_sensor.motion_detected", "off")

    hass_driver.set_state("binary_sensor.motion_detected", "on")

    turn_on = hass_driver.get_mock("turn_on")
    assert turn_on.call_count == 3
    turn_on.assert_has_calls(
        [mock.call("light.1"), mock.call("light.2"), mock.call("light.3")]
    )


@automation_fixture(
    LivingRoomMotion,
    args={
        "motion_entity": "binary_sensor.motion_detected",
        "light_entities": ["light.1", "light.2", "light.3"],
    },
)
def living_room_motion() -> LivingRoomMotion:
    pass
