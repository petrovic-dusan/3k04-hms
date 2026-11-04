import time

from hms.adc_comm_processor import ADCCommProcessor
from hms.alarm_handler import AlarmHandler
from hms.database_handler import DatabaseHandler
from hms.udp_adc_connect import UdpTransport
from hms.web_server import WebServer

from hms.config import *

def main() -> None:
    db = DatabaseHandler()
    transport = UdpTransport()
    processor = ADCCommProcessor(db, transport.send)
    alarms = AlarmHandler(db)
    web = WebServer()

    for unit_id in ADC_UNITS:
        processor.mark_seen(unit_id)

    print(f"HMS listening on {HMS_ADDRESS[0]}:{HMS_ADDRESS[1]}")
    print(f"Dashboard at http://{WEB_ADDRESS[0]}:{WEB_ADDRESS[1]}/")

    next_alarm = next_db_pull = time.monotonic()
    try:
        while True:
            for msg in transport.receive_all():
                processor.enqueue(msg)
            processor.main()

            now = time.monotonic()
            if now >= next_alarm:
                alarms.main()
                next_alarm = now + ALARM_CHECK_PERIOD
            if now >= next_db_pull:
                web.update(db.get_all_info())
                next_db_pull = now + GUI_REFRESH_PERIOD

            time.sleep(DT - (time.monotonic() - now))
    except KeyboardInterrupt:
        pass
    finally:
        web.stop()
        transport.close()


if __name__ == "__main__":
    main()
