from pydantic import BaseModel  # , Field, Validator
from typing import List


class Connection(BaseModel):
    status: bool = False
    latency: int = 200
    auto_ports: bool = True
    port_map: List[List[int]] = []

    def set_status(self, status: bool = None):
        if status is None:
            self.status = not self.status
        else:
            self.status = str2bool(status)

    def set_port_map(self, port_map: List[List[int]] = []):
        self.port_map = port_map

    def set_latency(self, latency: int):
        self.latency = int(latency)

    def set_auto_ports(self, auto_ports: bool):
        self.auto_ports = str2bool(auto_ports)


def str2bool(v):
    if type(v) == bool:
        return v
    else:
        return v.lower() in ['connect', 'true', 'on', '1']
