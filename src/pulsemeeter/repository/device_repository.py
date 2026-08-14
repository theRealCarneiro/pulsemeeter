'''
Device repository layer.
Handles device data storage and retrieval operations.
Works with existing ConfigModel structure.
'''
import logging
from typing import Optional, Any
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.config_model import ConfigModel

LOG = logging.getLogger("generic")


class DeviceRepository:
    '''
    Repository for managing device data storage and retrieval.
    '''

    def __init__(self, config: Optional[ConfigModel] = None):
        '''
        Initialize the device repository.

        Args:
            config: Optional ConfigModel instance. If None, loads from file.
        '''
        self.config_persistence = config
        self.config = config.get_config()
        self._devices = self.config.devices

    def create_device(self, device_dict: dict) -> tuple[str, str, DeviceModel]:
        '''
        Create a new device and save to config.

        Args:
            device_dict: Device configuration dictionary

        Returns:
            tuple of (device_type, device_id, device_model)
        '''
        device = DeviceModel(**device_dict)
        device_type = device.get_type()
        device_dicts = self._devices[device_type]
        device_id = max(device_dicts, key=int, default='0')
        device_id = str(int(device_id) + 1)
        device_dicts[device_id] = device
        return device_type, device_id, device

    def remove_device(self, device_type: str, device_id: str) -> DeviceModel:
        '''
        Remove a device and save to config.

        Args:
            device_type: Type of device
            device_id: Device identifier

        Returns:
            The removed device model
        '''
        device = self._devices[device_type].pop(device_id)
        return device

    def update_device(self, device_type: str, device_id: str, device_schema: dict) -> Optional[DeviceModel]:
        '''
        Update a device and save to config.

        Args:
            device_type: Type of device
            device_id: Device identifier
            device_schema: New device configuration

        Returns:
            Updated device model
        '''
        DeviceModel(**device_schema)
        device = self.get_device(device_type, device_id)
        device.update_device_settings(device_schema)

    def get_device(self, device_type: str, device_id: str) -> DeviceModel:
        '''
        Get a device by type and ID.

        Args:
            device_type: Type of device
            device_id: Device identifier

        Returns:
            Device model if found, None otherwise
        '''
        return self._devices[device_type].get(device_id)

    def get_devices_by_type(self, device_type: str) -> dict[str, DeviceModel]:
        '''
        Get all devices of a specific type.

        Args:
            device_type: Type of device ('vi', 'b', 'hi', 'a')

        Returns:
            dictionary of device_id -> DeviceModel
        '''
        return self._devices.get(device_type)

    def get_all_devices(self) -> dict[str, dict[str, DeviceModel]]:
        '''
        Get all devices.

        Returns:
            dictionary of device_type -> {device_id -> DeviceModel}
        '''
        return self._devices

    def find_device_by_key(self, key: str, value: Any, device_types: tuple[str] = None) -> tuple[str, str, DeviceModel]:
        '''
        Find device by name.

        Args:
            name: Device name to search for

        Returns:
            tuple of (device_type, device_id, device_model) or None if not found
        '''
        if device_types is None:
            device_types = ('vi', 'hi', 'a', 'b')

        res = []
        for device_type in device_types:
            for device_id, device in self._devices[device_type].items():
                if device.__dict__[key] == value:
                    res.append((device_type, device_id, device))

        return res

    def get_primary_device(self, device_type: str) -> tuple[str, str, DeviceModel]:
        '''
        Get the primary device of a specific type.

        Args:
            device_type: Type of device ('vi', 'b')

        Returns:
            Primary device model if found, None otherwise
        '''
        return self.find_device_by_key('primary', True, (device_type,))
