CHANNEL_MAPS = {
    "Mono": ["MONO"],

    "Stereo": ["FL", "FR"],
    "Stereo + FC + LFE": ["FC", "FL", "FR", "LFE"],
    "Stereo + RC + LFE": ["FL", "FR", "LFE", "RC"],

    "Quad": ["FL", "FR", "RL", "RR"],

    "5.1": ["FC", "FL", "FR", "LFE", "RL", "RR"],
    "5.1 Rear Center": ["FL", "FR", "LFE", "RC", "RL", "RR"],
    "5.1.2 Atmos Rear": ["FC", "FL", "FR", "LFE", "RL", "RR", "TRL", "TRR"],
    "5.1.2 Atmos Front": ["FC", "FL", "FR", "LFE", "RL", "RR", "TFL", "TFR"],

    "7.1": ["FC", "FL", "FR", "LFE", "RL", "RR", "SL", "SR"],
    "7.1 Rear Center": ["FL", "FR", "LFE", "RC", "RL", "RR", "SL", "SR"],
    "7.1.2 Atmos Rear": ["FC", "FL", "FR", "LFE", "RL", "RR", "SL", "SR", "TRL", "TRR"],
    "7.1.2 Atmos Front": ["FC", "FL", "FR", "LFE", "RL", "RR", "SL", "SR", "TFL", "TFR"],
    "7.1.4 Atmos Full": ["FC", "FL", "FR", "LFE", "RL", "RR", "SL", "SR", "TFL", "TFR", "TRL", "TRR"],
}

REVERSE_MAP = {tuple(v): k for k, v in CHANNEL_MAPS.items()}


CHANNEL_NAME_ALIASES = {
    'mono': 'MONO',
    'front-left': 'FL',
    'front-right': 'FR',
    'front-center': 'FC',
    'rear-left': 'RL',
    'rear-right': 'RR',
    'rear-center': 'RC',
    'lfe': 'LFE',
    'subwoofer': 'LFE',
    'side-left': 'SL',
    'side-right': 'SR',
    'top-front-left': 'TFL',
    'top-front-right': 'TFR',
    'top-front-center': 'TFC',
    'top-rear-left': 'TRL',
    'top-rear-right': 'TRR',
    'top-rear-center': 'TRC',
    'top-center': 'TC',
    'aux0': 'AUX0',
    'aux1': 'AUX1',
    'aux2': 'AUX2',
    'aux3': 'AUX3',
    'aux4': 'AUX4',
    'aux5': 'AUX5',
    'aux6': 'AUX6',
    'aux7': 'AUX7',
    'stereo-left': 'STL',
    'stereo-right': 'STR',
    'unknown': 'UNK',
}


def get_channel_map_name(channels):
    return REVERSE_MAP.get(tuple(channels), "unknown")
