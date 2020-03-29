# appdaemon-testing
Ergonomic and pythonic unit testing for AppDaemon apps. Utilities to allow you to test your AppDaemon home automation apps using all the _pythonic_ testing patterns you are already familiar with.

## Install

```sh
pip install appdaemon-testing
``` 

## Full Documentation

An enhanced, source-linked version of the documentation below as well as complete [API documentation](https://nickwhyte.com/appdaemon-testing/#header-submodules) is available [here](https://nickwhyte.com/appdaemon-testing/)

## Writing your first test

This demo assumes you will use [`pytest`](https://docs.pytest.org/en/latest/) as your test runner. Install the `appdaemon-testing` and [`pytest`](https://docs.pytest.org/en/latest/) packages:

```sh
pip install appdaemon-testing pytest
``` 

In your `appdaemon` configuration directory, introduce a new `tests` directory. This is where we are going to write the tests for your apps.

Additionally we also need to introduce an `__init__.py` file to `tests` and `apps` directories to make them an importable package. You should have a tree that looks something like this:

```
├── appdaemon.yaml
├── apps
│   ├── __init__.py
│   ├── apps.yaml
│   └── living_room_motion.py
├── dashboards
├── namespaces
└── tests
    ├── __init__.py
    └── test_living_room_motion.py
```

We have an automation, `apps/living_room_motion.py` that we wish to test. It looks like this:

```py
import appdaemon.plugins.hass.hassapi as hass


class LivingRoomMotion(hass.Hass):
    def initialize(self):
        self.listen_state(self.on_motion_detected, self.args["motion_entity"])

    def on_motion_detected(self, entity, attribute, old, new, kwargs):
        if old == "off" and new == "on":
            for light in self.args["light_entities"]:
                self.turn_on(light)
```

Create a new file, `tests/test_living_room_motion.py`. This is where we will write the tests for our automation.

First we will declare an _`appdaemon_testing.pytest.automation_fixture`_:

```py
@automation_fixture(
    LivingRoomMotion,
    args={
        "motion_entity": "binary_sensor.motion_detected",
        "light_entities": ["light.1", "light.2", "light.3"],
    },
)
def living_room_motion() -> LivingRoomMotion:
    pass
```


With this fixture, it's now possible to write some tests. We will first write a test to check the state listener callbacks are registered:

```py
def test_callbacks_are_registered(hass_driver, living_room_motion: LivingRoomMotion):
    listen_state = hass_driver.get_mock("listen_state")
    listen_state.assert_called_once_with(
        living_room_motion.on_motion_detected, "binary_sensor.motion_detected")
```

We use the `appdaemon_testing.pytest.hass_driver` fixture to obtain mock implementations of methods that exist on the AppDaemon Hass API. We can query these mocks and make assertions on their values. In this test we make an assertion that `listen_state` is called once with the specified parameters.

We will next write a test to make an assertion that the lights are turned on when motion is detected:

```py
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
```

This test uses the `HassDriver.setup()` context manager to set the initial state for testing. When execution is within `HassDriver.setup()` all state updates will not be triggered.

With the initial state configured, we can now proceed to triggering the state change (`HassDriver.set_state`). After the state change has occured, we can then begin to make assertions about calls made to the underlying API. In this test we wish to make assertions that `turn_on` is called. We obtain the `turn_on` mock implementation and make assertions about its calls and call count.  

You can see this full example and example directory structure within the [`example`](https://github.com/nickw444/appdaemon-testing/tree/master/example) directory in this repo.


## [`pytest`](https://docs.pytest.org/en/latest/) plugin

The `appdaemon_testing.pytest` package provides a handy `appdaemon_testing.pytest.hass_driver` fixture to allow you easy access to the global `HassDriver` instance. This fixture takes care of ensuring AppDaemon base class methods are patched.

Additionally, it provides a decorator, `appdaemon_testing.pytest.automation_fixture` which can be used to declare automation fixtures. It can be used like so:

```py
from appdaemon_testing.pytest import automation_fixture
from apps.living_room_motion import LivingRoomMotion


@automation_fixture(
    LivingRoomMotion,
    args={
        "motion_entity": "binary_sensor.motion_detected",
        "light_entities": ["light.1", "light.2", "light.3"],
    },
)
def living_room_motion() -> LivingRoomMotion:
    pass
```
