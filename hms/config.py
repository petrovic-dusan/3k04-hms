# total systekm operation freq
DT = 0.01

# alarma and gui refresh rates (s)
ALARM_CHECK_PERIOD = 0.5
GUI_REFRESH_PERIOD = 1.0

# ADC authorization
AUTHORIZED_PERSONNEL = ["nurse_001", "doctor_001"]

# adc disconnect timings (s)
OFFLINE_THRESHOLD = 15.0
SUSPECT_THRESHOLD = 9.0

# udp addresses for connection
HMS_ADDRESS = ("127.0.0.1", 5000)
WEB_ADDRESS = ("127.0.0.1", 8080)

# dummy adc unit connections
ADC_UNITS = {
    "adc_01": ("127.0.0.1", 5001),
    "adc_02": ("127.0.0.1", 5002),
    "adc_03": ("127.0.0.1", 5003),
}

# alarm manager med threshold
MED_THRESHOLDS = {
    "morphine": 20,
    "insulin": 15,
    "amoxicillin": 30,
}

LOG_PATH = "hms_event_log.log"