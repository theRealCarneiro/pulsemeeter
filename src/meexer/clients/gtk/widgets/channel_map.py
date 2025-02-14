from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


CHANNEL_MAPS = {
    "mono": ["mono"],
    "stereo": ["front-left", "front-right"],
    "quad": ["front-left", "front-right", "rear-left", "rear-right"],
    "5.0": ["front-left", "front-right", "front-center", "rear-left", "rear-right"],
    "5.1": ["front-left", "front-right", "front-center", "lfe", "rear-left", "rear-right"],
    "7.1": ["front-left", "front-right", "front-center", "lfe", "rear-left", "rear-right", "side-left", "side-right"]
}
