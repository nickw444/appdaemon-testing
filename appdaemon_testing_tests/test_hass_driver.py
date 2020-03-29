from unittest import mock

import pytest

from appdaemon_testing import HassDriver


def test_get_state(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light.1") == "off"


def test_get_state_attribute(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light.1", attribute="linkquality") == 60


def test_get_state_attribute_all(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light.1", attribute="all") == {"state": "off", "linkquality": 60}


def test_get_state_attribute_domain(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light") == {"light.1": "off", "light.2": "on"}


def test_get_state_attribute_domain_with_attribute(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light", attribute="linkquality") == {"light.1": 60, "light.2": 10}


def test_get_state_attribute_domain_with_attribute_all(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light", attribute="all") == {
        "light.1": {"state": "off", "linkquality": 60},
        "light.2": {"state": "on", "linkquality": 10, "brightness": 60},
    }


def test_get_state_with_default(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light.1", attribute="brightness", default=40) == 40
    assert get_state("light.2", attribute="brightness", default=40) == 60


def test_get_state_domain_with_default(hass_driver):
    get_state = hass_driver.get_mock("get_state")
    assert get_state("light", attribute="brightness", default=40) == {
        "light.1": 40,
        "light.2": 60,
    }


def test_listen_state(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler1 = mock.Mock()
    handler2 = mock.Mock()
    listen_state(handler1, "light.1")
    listen_state(handler2, "light.1")

    assert handler1.call_count == 0
    assert handler2.call_count == 0

    hass_driver.set_state("light.1", "off")

    assert handler1.call_count == 0
    assert handler2.call_count == 0

    hass_driver.set_state("light.1", "on")

    handler1.assert_called_once_with("light.1", "state", "off", "on", {})
    handler2.assert_called_once_with("light.1", "state", "off", "on", {})


def test_listen_state_attribute(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler = mock.Mock()
    listen_state(handler, "light.1", attribute="linkquality")

    assert handler.call_count == 0
    hass_driver.set_state("light.1", "on")
    assert handler.call_count == 0

    hass_driver.set_state("light.1", 50, attribute_name="linkquality")
    handler.assert_called_once_with("light.1", "linkquality", 60, 50, {})


def test_listen_state_attribute_all(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler = mock.Mock()
    listen_state(handler, "light.1", attribute="all")

    assert handler.call_count == 0
    hass_driver.set_state("light.1", 75, attribute_name="brightness")
    handler.assert_called_once_with(
        "light.1",
        None,
        {"state": "off", "linkquality": 60},
        {"state": "off", "linkquality": 60, "brightness": 75},
        {},
    )


def test_listen_state_domain(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler = mock.Mock()
    listen_state(handler, "light", attribute="brightness")

    assert handler.call_count == 0
    hass_driver.set_state("light.2", 75, attribute_name="brightness")
    handler.assert_called_once_with("light.2", "brightness", 60, 75, {})


def test_listen_state_with_new(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler = mock.Mock()
    listen_state(handler, "media_player.smart_tv", attribute="source", new="Spotify")

    hass_driver.set_state("media_player.smart_tv", "YouTube", attribute_name="source")
    assert handler.call_count == 0

    hass_driver.set_state("media_player.smart_tv", "Spotify", attribute_name="source")
    handler.assert_called_once_with(
        "media_player.smart_tv", "source", "YouTube", "Spotify", {}
    )


def test_listen_state_with_old(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler = mock.Mock()
    listen_state(handler, "media_player.smart_tv", attribute="source", old="Spotify")

    hass_driver.set_state("media_player.smart_tv", "Spotify", attribute_name="source")
    assert handler.call_count == 0

    hass_driver.set_state("media_player.smart_tv", "TV", attribute_name="source")
    handler.assert_called_once_with(
        "media_player.smart_tv", "source", "Spotify", "TV", {}
    )


def test_setup_does_not_trigger_spys(hass_driver):
    listen_state = hass_driver.get_mock("listen_state")
    handler = mock.Mock()
    listen_state(handler, "light")
    listen_state(handler, "light.1", attribute="brightness")

    with hass_driver.setup():
        hass_driver.set_state("light.1", "off")
        hass_driver.set_state("light.1", "on")
        hass_driver.set_state("light.1", 50, attribute_name="linkquality")

    assert handler.call_count == 0
    hass_driver.set_state("light.1", "off")
    assert handler.call_count == 1


@pytest.fixture
def hass_driver() -> HassDriver:
    hass_driver = HassDriver()
    hass_driver._states = {
        "light.1": {"state": "off", "linkquality": 60},
        "light.2": {"state": "on", "linkquality": 10, "brightness": 60},
        "media_player.smart_tv": {"state": "on", "source": None},
    }
    return hass_driver
