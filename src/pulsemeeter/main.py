'''
Entry point
'''
import logging

from pulsemeeter.settings import CONFIG_FILE
from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.clients.gtk.gtk_client import GtkClient
from pulsemeeter.clients.cli.cli_client import parse_args
from pulsemeeter.utils.config_persistence import ConfigPersistence
from pulsemeeter.repository.device_repository import DeviceRepository
from pulsemeeter.controller.device_controller import DeviceController

LOG = logging.getLogger("generic")


def start_gui():
    app = GtkClient()
    app.run()


def init_devices():
    ConfigModel.load_config()


def cleanup_devices():
    config_persistence = ConfigPersistence(ConfigModel, CONFIG_FILE)
    device_repository = DeviceRepository(config_persistence)
    device_controller = DeviceController(device_repository=device_repository)
    device_controller.cleanup()


def mute(device_type, device_id, state):
    config_persistence = ConfigPersistence(ConfigModel, CONFIG_FILE)
    device_repository = DeviceRepository(config_persistence)
    device_controller = DeviceController(device_repository=device_repository)
    device_controller.set_mute(device_type, device_id, state)


def volume(device_type, device_id, value):
    config_persistence = ConfigPersistence(ConfigModel, CONFIG_FILE)
    device_repository = DeviceRepository(config_persistence)
    device_controller = DeviceController(device_repository=device_repository)
    device_controller.set_volume(device_type, device_id, value)


def primary(device_type, device_id):
    config_persistence = ConfigPersistence(ConfigModel, CONFIG_FILE)
    device_repository = DeviceRepository(config_persistence)
    device_controller = DeviceController(device_repository=device_repository)
    device_controller.device_manager.set_primary(device_type, device_id)


def connect(input_type, input_id, output_type, output_id, state):
    config_persistence = ConfigPersistence(ConfigModel, CONFIG_FILE)
    device_repository = DeviceRepository(config_persistence)
    device_controller = DeviceController(device_repository=device_repository)
    device_controller.set_connection(input_type, input_id, output_type, output_id, state)


def main():

    arg_map = {
        None: start_gui,
        'init': init_devices,
        'cleanup': cleanup_devices,
        'mute': mute,
        'volume': volume,
        'primary': primary,
        'connect': connect
    }

    parsed = parse_args()
    command = parsed.command
    args = list(vars(parsed).values())[1:]
    arg_map[command](*args)

    return 0


if __name__ == '__main__':
    main()
