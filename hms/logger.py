import json
from datetime import datetime
from enum import Enum

from hms.config import LOG_PATH

EVENT_WIDTH = 16

def _fmt(value):
    # turn a field value into a single token for the log line
    if value is None:
        return "-"
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, float):
        return f"{value:.1f}"
    text = str(value)
    if text == "" or '"' in text or any(c.isspace() for c in text):
        return json.dumps(text)
    return text


def _alarm_fields(alert):
    # the fields that describe what an alarm is about (medicine/qty/threshold or unit_id/status)
    skip = ("id", "type", "raised_at", "active", "cleared_at")
    return {k: v for k, v in alert.items() if k not in skip}


class EventLogger:
    def __init__(self, path=LOG_PATH):
        self.path = path
        self.file = open(path, "a", encoding="utf-8", buffering=1)

    def _write(self, event, **fields):
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        details = " ".join(f"{key}={_fmt(value)}" for key, value in fields.items())
        self.file.write(f"{stamp} | {event:<{EVENT_WIDTH}} | {details}\n")

    def close(self):
        self.file.close()

    # SYSTEM -------------------------------
    def system_start(self, hms_address, web_address, units, med_thresholds):
        self._write(
            "HMS_START",
            hms=f"{hms_address[0]}:{hms_address[1]}",
            web=f"{web_address[0]}:{web_address[1]}",
            units=",".join(f"{u}@{a[0]}:{a[1]}" for u, a in units.items()),
            thresholds=",".join(f"{m}:{t}" for m, t in med_thresholds.items()),
        )

    def system_stop(self):
        self._write("HMS_STOP")

    # REQUESTS -------------------------------
    def request(self, msg, approved, reason, available, unit_status):
        self._write(
            "REQUEST_APPROVED" if approved else "REQUEST_DENIED",
            unit=msg.unit_id,
            request_id=msg.request_id,
            user=msg.user_id,
            medicine=msg.medicine,
            requested=msg.requested_qty,
            available=available,
            unit_status=unit_status,
            reason=reason,
        )

    # INVENTORY -------------------------------
    def inventory_update(self, unit_id, medicine, old_qty, new_qty):
        # old_qty is None the first time a unit reports a medicine
        self._write(
            "INVENTORY_UPDATE",
            unit=unit_id,
            medicine=medicine,
            old_qty=old_qty,
            new_qty=new_qty
        )

    # STATUS -------------------------------
    def status_change(self, unit_id, old_status, new_status):
        fields = {"unit": unit_id, "old": old_status, "new": new_status}
        self._write("STATUS_CHANGE", **fields)

    
    # ALARMS -------------------------------
    def alarm_raised(self, alert):
        self._write("ALARM_RAISED", alarm_id=alert["id"], type=alert["type"], **_alarm_fields(alert))

    def alarm_updated(self, alert):
        self._write(
            "ALARM_UPDATED",
            alarm_id=alert["id"],
            type=alert["type"],
            medicine=alert["medicine"],
            new_qty=alert["qty"],
            threshold=alert["threshold"],
        )

    def alarm_cleared(self, alert):
        # reason is "resolved" (condition went away) or "superseded" (replaced by a new alarm)
        self._write(
            "ALARM_CLEARED",
            alarm_id=alert["id"],
            type=alert["type"],
            **_alarm_fields(alert)
        )

    # BAD INPUT / COMMS -------------------------------
    def msg_rejected(self, reason, unit_id):
        fields = {"reason": reason, "unit": unit_id}
        self._write("MSG_REJECTED", **fields)