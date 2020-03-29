import appdaemon.plugins.hass.hassapi as hass


class LivingRoomMotion(hass.Hass):
    def initialize(self):
        self.listen_state(self.on_motion_detected, self.args["motion_entity"])

    def on_motion_detected(self, entity, attribute, old, new, kwargs):
        if old == "off" and new == "on":
            for light in self.args["light_entities"]:
                self.turn_on(light)
