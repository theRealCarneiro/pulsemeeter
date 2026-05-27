import logging

from pydantic import BaseModel, root_validator, validator
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.connection_model import ConnectionModel

LOG = logging.getLogger("generic")

DEVICE_TYPES = ('vi', 'hi', 'a', 'b')
INPUT_TYPES = ('vi', 'hi')
OUTPUT_TYPES = ('a', 'b')
VIRTUAL_TYPES = ('vi', 'b')


class ConfigModel(BaseModel):
    '''
    Model for the config file. A root_validator runs after construction to
    repair self-inconsistent state (orphan connections, missing entries,
    out-of-range port_maps, duplicate primaries, empty-name devices) so the
    rest of the app never has to defend against invalid config shapes.
    '''

    devices: dict[str, dict[str, DeviceModel]] = {'vi': {}, 'hi': {}, 'a': {}, 'b': {}}
    vumeters: bool = True
    cleanup: bool = False
    tray: bool = False
    layout: str = 'Blocks'
    window_width: int = 800
    window_height: int = 600

    @validator('layout')
    def capitalize_layout(cls, v):
        return v.capitalize()

    @root_validator(skip_on_failure=True)
    def heal_invariants(cls, values):
        devices = values['devices']
        cls._ensure_device_buckets(devices)
        cls._drop_invalid_devices(devices)
        cls._dedupe_primary(devices)
        cls._repair_connections(devices)
        return values

    @classmethod
    def _ensure_device_buckets(cls, devices):
        for device_type in DEVICE_TYPES:
            devices.setdefault(device_type, {})

    @classmethod
    def _drop_invalid_devices(cls, devices):
        for device_type, bucket in devices.items():
            invalid_ids = [did for did, dev in bucket.items() if not dev.name.strip()]
            for device_id in invalid_ids:
                LOG.warning("ConfigModel: dropping %s/%s with empty name", device_type, device_id)
                bucket.pop(device_id)

    @classmethod
    def _dedupe_primary(cls, devices):
        for device_type in VIRTUAL_TYPES:
            seen_primary = False
            for device_id, device in devices[device_type].items():
                if device.primary is not True:
                    continue
                if seen_primary:
                    LOG.warning("ConfigModel: clearing duplicate primary on %s/%s", device_type, device_id)
                    device.primary = False
                else:
                    seen_primary = True

    @classmethod
    def _repair_connections(cls, devices):
        for input_type in INPUT_TYPES:
            for input_id, input_device in devices[input_type].items():
                cls._ensure_connection_buckets(input_device)
                cls._drop_orphan_connections(devices, input_type, input_id, input_device)
                cls._fill_missing_connections(devices, input_type, input_id, input_device)
                cls._repair_port_maps(devices, input_type, input_id, input_device)

    @classmethod
    def _ensure_connection_buckets(cls, input_device):
        for output_type in OUTPUT_TYPES:
            input_device.connections.setdefault(output_type, {})

    @classmethod
    def _drop_orphan_connections(cls, devices, input_type, input_id, input_device):
        for output_type in OUTPUT_TYPES:
            output_bucket = devices[output_type]
            orphan_ids = [oid for oid in input_device.connections[output_type] if oid not in output_bucket]
            for output_id in orphan_ids:
                LOG.warning(
                    "ConfigModel: dropping orphan connection %s/%s -> %s/%s",
                    input_type, input_id, output_type, output_id,
                )
                input_device.connections[output_type].pop(output_id)

    @classmethod
    def _fill_missing_connections(cls, devices, input_type, input_id, input_device):
        for output_type in OUTPUT_TYPES:
            for output_id, output_device in devices[output_type].items():
                if output_id in input_device.connections[output_type]:
                    continue
                LOG.warning(
                    "ConfigModel: filling missing connection %s/%s -> %s/%s",
                    input_type, input_id, output_type, output_id,
                )
                input_device.connections[output_type][output_id] = ConnectionModel(
                    nick=output_device.nick,
                    input_sel_channels=_default_sel_channels(input_device),
                    output_sel_channels=_default_sel_channels(output_device),
                )

    @classmethod
    def _repair_port_maps(cls, devices, input_type, input_id, input_device):
        for output_type in OUTPUT_TYPES:
            for output_id, connection in input_device.connections[output_type].items():
                output_device = devices[output_type][output_id]
                if _port_map_in_range(connection.port_map, input_device.channels, output_device.channels):
                    continue
                LOG.warning(
                    "ConfigModel: resetting invalid port_map %s/%s -> %s/%s",
                    input_type, input_id, output_type, output_id,
                )
                connection.port_map = []
                connection.auto_ports = True


def _default_sel_channels(device):
    if device.selected_channels:
        return list(device.selected_channels)
    return [True] * device.channels


def _port_map_in_range(port_map, input_channels, output_channels):
    if not port_map:
        return True
    if len(port_map) > input_channels:
        return False
    for targets in port_map:
        for target in targets:
            if target < 0 or target >= output_channels:
                return False
    return True
