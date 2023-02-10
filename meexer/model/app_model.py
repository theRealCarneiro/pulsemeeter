import pulsectl

INPUT = 0  # source outputs
OUTPUT = 1  # sink inputs


def filter_results(app):
    # filter pavu and pm peak sinks
    return (
        'application.name' in app.proplist,
        '_peak' not in app.proplist['application.name'],
        app.proplist.get('application.id') != 'org.PulseAudio.pavucontrol'
    )


def list_outputs(app):
    pass


def list_sink_inputs(index=None, pulse=None):
    si_list = None

    # get device list or single device
    if index is not None:
        try:
            device = pulse.sink_input_info(int(index))
        except pulsectl.PulseIndexError:
            return []
        si_list = [device]
    else:
        si_list = pulse.sink_input_list()

    app_list = []
    for app in si_list:

        # filter pavu and pm peak sinks
        try:
            filter(app)
        except AssertionError:
            continue

        # some apps don't have icons
        icon = app.proplist.get('application.icon_name')
        if icon is None:
            icon = 'audio-card'

        index = app.index
        label = app.proplist['application.name']
        volume = int(app.volume.values[0] * 100)
        device = pulse.sink_info(app.sink)
        app_list.append((index, label, icon, volume, device.name))
    return app_list


def list_source_outputs(index=None, pulse=None):
    if index is not None:
        try:
            device = pulse.source_output_info(int(index))
        except pulsectl.PulseIndexError:
            return []
        si_list = [device]
    else:
        si_list = pulse.source_output_list()

    app_list = []
    for app in si_list:

        # filter pavu and pm peak sinks
        try:
            filter(app)
        except AssertionError:
            continue

        # some apps don't have icons
        icon = app.proplist.get('application.icon_name')
        if icon is None:
            icon = 'audio-card'

        index = app.index
        icon = app.proplist['application.icon_name']
        label = app.proplist['application.name']
        volume = int(app.volume.values[0] * 100)
        device = pulse.source_info(app.source)
        app_list.append((index, label, icon, volume, device.name))
    return app_list
