from unittest import mock

from appdaemon_testing.pytest import automation_fixture
from apps.living_room_motion import LivingRoomMotion


def test_callbacks_are_registered(hass_driver, living_room_motion: LivingRoomMotion):
    listen_state = hass_driver.get_mock("listen_state")
    assert listen_state.call_count == 1
    listen_state.assert_has_calls(
        [
            mock.call(
                living_room_motion.on_motion_detected, "binary_sensor.motion_detected"
            )
        ]
    )


def test_lights_are_turned_on_when_motion_detected(
    hass_driver, living_room_motion: LivingRoomMotion
):
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
