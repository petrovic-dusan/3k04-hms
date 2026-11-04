import itertools
import time

from hms.hms_enums import Status

QTY_ALERT = "inventoryLow"
STATUS_ALERT = "unitStatus"


class DatabaseHandler:
    def __init__(self):
        self.clock =  time.monotonic
        self.inventory = {}
        self.statuses = {}
        self.alerts = []

    # REGULAR GET/SET -------------------------------
    def update_medicine_count(self, unit_id, medicine, new_qty):
        # setdefault also covers the case where a new medicine is inserted for the first time
        self.inventory.setdefault(unit_id, {})[medicine] = new_qty

    def get_inventory(self, medicine):
        return sum(meds.get(medicine, 0) for meds in self.inventory.values())

    def get_unit_inventory(self, unit_id, medicine):
        return self.inventory.get(unit_id, {}).get(medicine, 0)

    def get_status(self, unit_id):
        return self.statuses[unit_id]

    def set_status(self, unit_id, status):
        self.statuses[unit_id] = status

    def get_unit_ids(self):
        return list(self.statuses)

    # ALARM MANAGEMENT -------------------------------
    def find_existing(self, alert_type, key, value):
            for alert in self.alerts:
                if alert["active"] and alert["type"] == alert_type and alert.get(key) == value:
                    return alert
            return None

    def add(self, fields):
        self.alerts.append(
            {**fields, "raised_at": self.clock(),
                "active": True, "cleared_at": None}
        )

    def clear(self, alert):
        if alert is not None:
            alert["active"] = False
            alert["cleared_at"] = self.clock()

    def raise_qty_alarm(self, medicine, qty, threshold):
        # check if a quantity alarm already exists for a given medicine
        alert = self.find_existing(QTY_ALERT, "medicine", medicine)
        #if exists just update qty
        if alert is not None:
            alert["qty"], alert["threshold"] = qty, threshold
            return
        # if not, add new alarm
        self.add({"type": QTY_ALERT, "medicine": medicine, "qty": qty, "threshold": threshold})

    def clear_qty_alarm(self, medicine):
        self.clear(self.find_existing(QTY_ALERT, "medicine", medicine))

    def raise_status_alarm(self, unit_id, status):
        alert = self.find_existing(STATUS_ALERT, "unit_id", unit_id)
        if alert is not None:
            if alert["status"] == status.value:
                return
            self.clear(alert)
        self.add({"type": STATUS_ALERT, "unit_id": unit_id, "status": status.value})

    def clear_status_alarm(self, unit_id):
        self.clear(self.find_existing(STATUS_ALERT, "unit_id", unit_id))

    # FOR GUI ------
    def get_active_alerts(self):
        return [a for a in self.alerts if a["active"]]

    def get_all_info(self):
        return {
            "stamp": self.clock(),
            "units": [
                {"unit_id": u, "status": s.value} for u, s in sorted(self.statuses.items())
            ],
            "inventory": [
                {"unit_id": u, "medicine": m, "qty": q}
                for u, meds in sorted(self.inventory.items())
                for m, q in sorted(meds.items())
            ],
            "alerts": [
                {
                    "type": a["type"],
                    "unit_id": a.get("unit_id", ""),
                    "status": a.get("status", ""),
                    "medicine": a.get("medicine", ""),
                    "qty": a.get("qty", 0),
                    "threshold": a.get("threshold", 0),
                    "raised_at": a["raised_at"],
                }
                for a in self.get_active_alerts()
            ],
        }

