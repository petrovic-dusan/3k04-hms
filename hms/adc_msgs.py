from hms.hms_enums import MessageType, Status


class AdcMsg:
    def __init__(self, data):
        # data is basically the json asa dictionary
        extra = data.get("additional_fields") or {}
        #mandatory
        self.unit_id = data["unit_id"]
        try:
            self.message_type = MessageType(data["message_type"])
        except ValueError:
            self.message_type = data["message_type"]
        #optional fields
        self.medicine = extra.get("medicine")
        self.new_qty = extra.get("new_qty")
        self.requested_qty = extra.get("requested_qty")
        self.user_id = extra.get("user_id")
        self.request_id = extra.get("request_id")
        self.status = Status(extra["status"]) if extra.get("status") is not None else None


class ResponseMessage:
    def __init__(self, request_id=None, approved=False):
        self.request_id = request_id
        self.approved = approved

    def to_dict(self):
        return {"request_id": self.request_id, "approved": self.approved}