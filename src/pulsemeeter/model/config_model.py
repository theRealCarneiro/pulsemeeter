import logging

from pydantic import BaseModel, field_validator, model_validator
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.connection_model import ConnectionModel

LOG = logging.getLogger("generic")

DEVICE_TYPES = ('vi', 'hi', 'a', 'b')
INPUT_TYPES = ('vi', 'hi')
OUTPUT_TYPES = ('a', 'b')
VIRTUAL_TYPES = ('vi', 'b')


class ConfigModel(BaseModel):
    '''
    Model for the config file. A model_validator runs after construction to
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

    @field_validator('layout')
    @classmethod
    def capitalize_layout(cls, v):
        return v.capitalize()

    @model_validator(mode='after')
    def heal_invariants(self):
        self._ensure_device_buckets()
        self._drop_invalid_devices()
        self._dedupe_primary()
        self._repair_connections()
        return self

    def _ensure_device_buckets(self):
        for device_type in DEVICE_TYPES:
            self.devices.setdefault(device_type, {})

    def _drop_invalid_devices(self):
        for device_type, bucket in self.devices.items():
            invalid_ids = [did for did, dev in bucket.items() if not dev.name.strip()]
            for device_id in invalid_ids:
                LOG.warning("ConfigModel: dropping %s/%s with empty name", device_type, device_id)
                bucket.pop(device_id)

    def _dedupe_primary(self):
        for device_type in VIRTUAL_TYPES:
            seen_primary = False
            for device_id, device in self.devices[device_type].items():
                if device.primary is not True:
                    continue
                if seen_primary:
                    LOG.warning("ConfigModel: clearing duplicate primary on %s/%s", device_type, device_id)
                    device.primary = False
                else:
                    seen_primary = True

    def _repair_connections(self):
        for input_type in INPUT_TYPES:
            for input_id, input_device in self.devices[input_type].items():
                self._ensure_connection_buckets(input_device)
                self._drop_orphan_connections(input_type, input_id, input_device)
                self._fill_missing_connections(input_type, input_id, input_device)
                self._repair_port_maps(input_type, input_id, input_device)

    def _ensure_connection_buckets(self, input_device):
        for output_type in OUTPUT_TYPES:
            input_device.connections.setdefault(output_type, {})

    def _drop_orphan_connections(self, input_type, input_id, input_device):
        for output_type in OUTPUT_TYPES:
            output_bucket = self.devices[output_type]
            orphan_ids = [oid for oid in input_device.connections[output_type] if oid not in output_bucket]
            for output_id in orphan_ids:
                LOG.warning(
                    "ConfigModel: dropping orphan connection %s/%s -> %s/%s",
                    input_type, input_id, output_type, output_id,
                )
                input_device.connections[output_type].pop(output_id)

    def _fill_missing_connections(self, input_type, input_id, input_device):
        for output_type in OUTPUT_TYPES:
            for output_id, output_device in self.devices[output_type].items():
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

    def _repair_port_maps(self, input_type, input_id, input_device):
        for output_type in OUTPUT_TYPES:
            for output_id, connection in input_device.connections[output_type].items():
                output_device = self.devices[output_type][output_id]
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
