import json
import select
import socket
import time
import uuid
from pathlib import Path

import yaml

from hms.config import ADC_UNITS, HMS_ADDRESS

CONFIG = Path(__file__).with_name("fake_adcs.yaml")
STATUSES = {"OK", "FAULT", "SUSPECT", "OFFLINE"}
REPLY_TIMEOUT = 1.0
SETTLE = 0.2


def known(unit_id, section):
    if unit_id in ADC_UNITS:
        return True
    print(f"{section}: skipping {unit_id}, not in ADC_UNITS in hms/config.py")
    return False


def load():
    config = yaml.safe_load(CONFIG.read_text()) or {}

    statuses = {}
    for unit_id, status in ((config.get("status") or {}).get("units") or {}).items():
        if not known(unit_id, "status"):
            continue
        status = str(status).upper()
        if status not in STATUSES:
            print(f"status: {unit_id} has unknown status {status!r}, using OK")
            status = "OK"
        statuses[unit_id] = status

    stock = {}
    for unit_id, medicines in ((config.get("inventory") or {}).get("units") or {}).items():
        if known(unit_id, "inventory"):
            stock[unit_id] = {m: int(q) for m, q in (medicines or {}).items()}

    print(f"loaded {CONFIG.name}")
    return config, statuses, stock


def send(sockets, unit_id, message_type, fields):
    message = {"unit_id": unit_id, "message_type": message_type, "additional_fields": fields}
    sockets[unit_id].sendto(json.dumps(message).encode(), HMS_ADDRESS)


def send_statuses(sockets, statuses):
    for unit_id, status in statuses.items():
        send(sockets, unit_id, "STATUS", {"status": status})


def send_inventory(sockets, stock):
    for unit_id, medicines in stock.items():
        for medicine, qty in medicines.items():
            send(sockets, unit_id, "INVENTORY", {"medicine": medicine, "new_qty": qty})


def send_request(sockets, req, pending):
    unit_id = req.get("unit_id")
    if unit_id not in sockets:
        print(f"request not sent: unit_id {unit_id!r} is not in ADC_UNITS in hms/config.py")
        return
    request_id = uuid.uuid4().hex[:8]
    fields = {"request_id": request_id}
    for key, field in (("user_id", "user_id"), ("medicine", "medicine"), ("qty", "requested_qty")):
        if key in req:
            fields[field] = req[key]
    pending[request_id] = {"unit_id": unit_id, "fields": fields, "sent_at": time.monotonic()}
    send(sockets, unit_id, "REQUEST", fields)


def describe(req):
    f = req["fields"]
    return (f"{req['unit_id']}: {f.get('user_id', '<no user>')} wants "
            f"{f.get('requested_qty', '<no qty>')} x {f.get('medicine', '<no medicine>')}")


def handle_replies(sockets, stock, inventory_enabled, pending, timeout):
    readable, _, _ = select.select(list(sockets.values()), [], [], timeout)
    for sock in readable:
        try:
            reply = json.loads(sock.recv(4096))
        except (ConnectionRefusedError, ValueError):
            continue
        req = pending.pop(reply.get("request_id"), None)
        if req is None:
            continue
        approved = reply.get("approved")
        print(f"{describe(req)} -> {'APPROVED' if approved else 'DENIED'}")

        unit_id = req["unit_id"]
        medicine, qty = req["fields"].get("medicine"), req["fields"].get("requested_qty")
        medicines = stock.get(unit_id, {})
        if approved and medicine in medicines and isinstance(qty, int):
            medicines[medicine] -= qty
            if inventory_enabled:
                send(sockets, unit_id, "INVENTORY", {"medicine": medicine, "new_qty": medicines[medicine]})

    now = time.monotonic()
    for request_id, req in list(pending.items()):
        if now - req["sent_at"] > REPLY_TIMEOUT:
            print(f"{describe(req)} -> no reply (HMS rejected the request)")
            del pending[request_id]


def next_time(now, period):
    period = float(period or 0)
    return now + period if period > 0 else None


def main():
    sockets = {}
    for unit_id, address in ADC_UNITS.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(address)
        sockets[unit_id] = sock

    config, statuses, stock = load()
    mtime = seen_mtime = CONFIG.stat().st_mtime
    changed_at = None
    pending = {}
    next_status = next_inventory = next_request = time.monotonic()
    print(f"sending to HMS at {HMS_ADDRESS[0]}:{HMS_ADDRESS[1]}, Ctrl+C to stop")

    try:
        while True:
            now = time.monotonic()
            current = CONFIG.stat().st_mtime
            if current != seen_mtime:
                seen_mtime, changed_at = current, now
            if changed_at is not None and now - changed_at >= SETTLE and seen_mtime != mtime:
                mtime, changed_at = seen_mtime, None
                try:
                    old = config
                    config, statuses, stock = load()
                    next_status = now
                    if config.get("inventory") != old.get("inventory"):
                        next_inventory = now
                    if config.get("request") != old.get("request"):
                        next_request = now
                except (yaml.YAMLError, ValueError, TypeError, AttributeError) as e:
                    print(f"{CONFIG.name} not reloaded: {e}")

            status_cfg = config.get("status") or {}
            inventory_cfg = config.get("inventory") or {}
            request_cfg = config.get("request") or {}
            inventory_enabled = bool(inventory_cfg) and inventory_cfg.get("enabled", True)
            request_enabled = bool(request_cfg) and request_cfg.get("enabled", True)

            if now >= next_status:
                send_statuses(sockets, statuses)
                next_status = now + float(status_cfg.get("period", 1.0))

            if inventory_enabled and next_inventory is not None and now >= next_inventory:
                send_inventory(sockets, stock)
                next_inventory = next_time(now, inventory_cfg.get("period"))

            if request_enabled and next_request is not None and now >= next_request:
                send_request(sockets, request_cfg, pending)
                next_request = next_time(now, request_cfg.get("period"))

            handle_replies(sockets, stock, inventory_enabled, pending, timeout=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        for sock in sockets.values():
            sock.close()


if __name__ == "__main__":
    main()
