from meexer.schemas.ipc_schema import Route


class Router:
    __routes = {}

    @classmethod
    def command(cls, command_str, flags=0, notify=True, save_config=True):
        '''
        Decorator for creating routes
        '''
        def decorator(function):
            route = Route(
                command=function,
                # make sure to include ALL flag
                flags=flags | 1 if flags != 0 else 0,
                notify=notify,
                save_config=save_config
            )
            cls.__routes[command_str] = route
            return function

        return decorator

    @classmethod
    def get_route(cls, command):
        return cls.__routes.get(command)
