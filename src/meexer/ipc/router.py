import logging
from typing import get_type_hints

from meexer.schemas.ipc_schema import Route

LOG = logging.getLogger("generic")


class Blueprint:
    routes = {}

    def __init__(self, name: str):
        self.name = name

    def command(self, command_str, flags=0, notify=True, save_config=True):
        '''
        Decorator for creating routes
        '''
        # quick hack to get the type hint
        def decorator(function):
            type_hints = list(get_type_hints(function).values())

            route = Route(
                command=function,
                schema_hint=type_hints[0] if len(type_hints) > 0 else None,
                # make sure to include ALL flag
                flags=flags | 1 if flags != 0 else 0,
                notify=notify,
                save_config=save_config
            )

            self.routes[command_str] = route
            return function

        return decorator
