import logging
from gettext import gettext as _
from typing import Any, Dict, Union

from blueman.bluez.Device import Device
from blueman.gui.Notification import Notification, _NotificationBubble, _NotificationDialog
from blueman.main.BatteryWatcher import BatteryWatcher
from blueman.plugins.AppletPlugin import AppletPlugin
from gi.repository import GLib


class ConnectionNotifier(AppletPlugin):
    __author__ = "cschramm"
    __icon__ = "bluetooth-symbolic"
    __description__ = _("Shows desktop notifications when devices get connected or disconnected.")

    __gsettings__ = {
        "schema": "org.blueman.plugins.connectionnotifier",
        "path": None
    }
    __options__ = {
        "battery-update": {
            "type": bool,
            "default": True,
            "name": _("battery-update"),
            "desc": _("Show notifications when battery updates."),
        }
    }

    _notifications: Dict[str, Union[_NotificationBubble, _NotificationDialog]] = {}

    def on_load(self) -> None:
        if self.get_option("battery-update"):
            self._battery_watcher = BatteryWatcher(self._on_battery_update)
        else:
            self._battery_watcher = None

    def on_unload(self) -> None:
        if self._battery_watcher is not None:
            del self._battery_watcher

    def on_device_property_changed(self, path: str, key: str, value: Any) -> None:
        # Reload option
        if self.get_option("battery-update"):
            if self._battery_watcher is None:
                self._battery_watcher = BatteryWatcher(self._on_battery_update)
        else:
            if self._battery_watcher is not None:
                del self._battery_watcher
                self._battery_watcher = None

        if key == "Connected":
            device = Device(obj_path=path)
            if value:
                self._notifications[path] = notification = Notification(
                    device.display_name,
                    _('Connected'),
                    icon_name=device["Icon"]
                )
                notification.show()
            else:
                Notification(device.display_name, _('Disconnected'), icon_name=device["Icon"]).show()

    def _on_battery_update(self, path: str, value: int) -> None:
        notification = self._notifications.get(path, None)
        if notification:
            try:
                notification.set_message(f"{_('Connected')} {value}%")
                notification.set_notification_icon("battery")
            except GLib.Error:
                logging.error("Failed to update notification", exc_info=True)
