import time
from collections import deque

from hms.config import AUTHORIZED_PERSONNEL, OFFLINE_THRESHOLD, SUSPECT_THRESHOLD
from hms.database_handler import DatabaseHandler
from hms.hms_enums import MessageType, Status
from hms.adc_msgs import AdcMsg, ResponseMessage

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_MSG = 2

class ADCCommProcessor:
    def __init__(self, dbhandler, publishFn):
        self.dbhandler = dbhandler
        self.publish = publishFn
        self.clock = time.monotonic
        self.q =  deque()
        self.known_adcs = {}

    def enqueue(self, msg):
        # for incoming messages, update frehsness and put in q for further processing
        self.mark_seen(msg.unit_id)
        self.q.append(msg)

    def main(self):
        # check for any stale adcs
        self.check_freshness()
        if len(self.q) == 0:
            return EXIT_NO_MSG
        return self.route_msg(self.q.popleft())

    def mark_seen(self, unit_id):
        self.known_adcs[unit_id] = self.clock()

    def check_freshness(self):
        now = self.clock()
        for unit_id, last_seen in self.known_adcs.items():
            if now - last_seen > OFFLINE_THRESHOLD:
                self.dbhandler.set_status(unit_id, Status.OFFLINE)
            elif now - last_seen > SUSPECT_THRESHOLD:
                self.dbhandler.set_status(unit_id, Status.SUSPECT)

    def route_msg(self, msg):
        if msg.message_type == MessageType.REQUEST:
            return self.process_request_msg(msg)
        if msg.message_type == MessageType.STATUS:
            return self.process_status_msg(msg)
        if msg.message_type == MessageType.INVENTORY:
            return self.process_inventory_msg(msg)
        return EXIT_ERROR

    def process_request_msg(self, msg):
        try:
            qty_available = self.dbhandler.get_unit_inventory(msg.unit_id, msg.medicine)
            response_approval = (self.dbhandler.get_status(msg.unit_id) == Status.OK
                                and self.validate_user(msg.user_id)
                                and msg.requested_qty <= qty_available)
            response = ResponseMessage(request_id=msg.request_id, approved=response_approval)
            self.publish(msg.unit_id, response.to_dict())
            return EXIT_OK
        except Exception:
            return EXIT_ERROR

    def validate_user(self, user_id):
        return user_id in AUTHORIZED_PERSONNEL

    def process_status_msg(self, msg):
        # check fields are correctly populated
        if msg.status is None:
            return EXIT_ERROR
        self.dbhandler.set_status(msg.unit_id, msg.status)
        return EXIT_OK

    def process_inventory_msg(self, msg):
        # check optional fields are correctly populated
        if msg.medicine is None or msg.new_qty is None:
            return EXIT_ERROR
        self.dbhandler.update_medicine_count(msg.unit_id, msg.medicine, msg.new_qty)
        return EXIT_OK
