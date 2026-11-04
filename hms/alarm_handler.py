from hms.hms_enums import Status
from hms.config import MED_THRESHOLDS
class AlarmHandler:
    def __init__(self, dbhandler):
        self.dbhandler = dbhandler
        self.med_thresholds = MED_THRESHOLDS

    def main(self):
        for medicine, threshold in self.med_thresholds.items():
            qty = self.dbhandler.get_inventory(medicine)
            if qty < threshold:
                self.dbhandler.raise_qty_alarm(medicine, qty, threshold)
            else:
                self.dbhandler.clear_qty_alarm(medicine)

        for unit_id in self.dbhandler.get_unit_ids():
            status = self.dbhandler.get_status(unit_id)
            if status != Status.OK:
                self.dbhandler.raise_status_alarm(unit_id, status)
            else:
                self.dbhandler.clear_status_alarm(unit_id)
