from typing import Callable


class SignalEntry:

    def __init__(self, callback: Callable):
        self.callback: Callable = callback
        self.blocked: bool = False


class SignalModel:

    def __init__(self):
        self._signals: dict[str, list[SignalEntry]] = {}

    def connect(self, signal_name: str, callback: Callable, *args, **kwargs) -> int:
        '''
        Register a callback for a signal and return its index.
        '''
        if signal_name not in self._signals:
            self._signals[signal_name] = []

        entry = SignalEntry(callback=callback)
        self._signals[signal_name].append((entry, args, kwargs))

        # Return the index of the new callback
        return len(self._signals[signal_name]) - 1

    def emit(self, signal_name: str, *args, **kwargs):
        '''
        Call all non-blocked callbacks associated with the signal.
        '''
        for entry, entry_args, entry_kwargs in self._signals.get(signal_name, []):
            if not entry.blocked:
                entry.callback(*(args + entry_args), **{**kwargs, **entry_kwargs})
