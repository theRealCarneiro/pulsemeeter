import json

from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.utils.config_persistence import ConfigPersistence


def _device_dict(name='vi_a', channels=2):
    return {
        'name': name,
        'channels': channels,
        'channel_list': ['front-left', 'front-right'][:channels],
        'selected_channels': [True] * channels,
        'device_type': 'source',
        'device_class': 'virtual',
        'primary': False,
    }


def test_load_self_heals_orphan_connection(tmp_path):
    path = tmp_path / 'config.json'
    payload = {
        'devices': {
            'vi': {
                '1': {
                    **_device_dict(name='vi_a'),
                    'connections': {
                        'a': {},
                        'b': {
                            '99': {
                                'nick': 'ghost',
                                'input_sel_channels': [True, True],
                                'output_sel_channels': [True, True],
                            }
                        },
                    },
                }
            },
            'hi': {},
            'a': {},
            'b': {},
        }
    }
    path.write_text(json.dumps(payload))

    config = ConfigPersistence(ConfigModel, str(path)).get_config()
    assert config.devices['vi']['1'].connections['b'] == {}
