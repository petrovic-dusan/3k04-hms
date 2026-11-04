from __future__ import annotations

import json
import socket

from hms.adc_msgs import AdcMsg
from hms.config import  HMS_ADDRESS, ADC_UNITS

class UdpTransport:
    def __init__(self, address: tuple[str, int] = HMS_ADDRESS, units: dict[str, tuple[str, int]] = ADC_UNITS) -> None:
        self.units = units
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(address)
        self.sock.setblocking(False)

    def receive_all(self) -> list[AdcMsg]:
        msgs = []
        while True:
            try:
                data, sender = self.sock.recvfrom(4096)
            except BlockingIOError:
                return msgs
            except ConnectionRefusedError:
                continue
            try:
                AdcMsg = AdcMsg.from_dict(json.loads(data))
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            if self.units.get(AdcMsg.unit_id) == sender:
                msgs.append(AdcMsg)

    def send(self, unit_id: str, payload: dict) -> None:
        try:
            self.sock.sendto(json.dumps(payload).encode(), self.units[unit_id])
        except ConnectionRefusedError:
            pass

    def close(self) -> None:
        self.sock.close()
