from hms.hms_enums import MessageType, Status
from dataclasses import asdict

class AdcMsg:
    #mandatory
    unit_id
    message_type : str
    #optional fields
    medicine = None
    new_qty = None
    requested_qty = None
    user_id = None
    request_id = None
    status = None

    def from_dict(cls, data) -> AdcMsg:
        # data is basically the json asa dictionary
        extra = data.get("additional_fields") or {}
        try:
            message_type: MessageType(data["message_type"])
        except ValueError:
            message_type = data["message_type"]
        return cls(
            unit_id=data["unit_id"],
            message_type=message_type,
            medicine=extra.get("medicine"),
            new_qty=extra.get("new_qty"),
            requested_qty=extra.get("requested_qty"),
            user_id=extra.get("user_id"),
            request_id=extra.get("request_id"),
            status=Status(extra.get("status")) if extra.get("status") is not None else None,
        )
    
class ResponseMessage:
    request_id: str = None
    approved: bool = False

    def to_dict(self):
        return asdict(self)