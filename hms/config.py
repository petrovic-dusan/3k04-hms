DT = 0.01
ALARM_PERIOD = 1.0
SNAPSHOT_PERIOD = 0.5
AUTHORIZED_PERSONNEL = ["nurse_001", "doctor_001"]
OFFLINE_THRESHOLD = 15.0
SUSPECT_THRESHOLD = 9.0

HMS_ADDRESS = ("127.0.0.1", 5000)
WEB_ADDRESS = ("127.0.0.1", 8080)

ADC_UNITS = {
    "adc_01": ("127.0.0.1", 5001),
    "adc_02": ("127.0.0.1", 5002),
    "adc_03": ("127.0.0.1", 5003),
}

MED_THRESHOLDS = {
    "morphine": 20,
    "insulin": 15,
    "amoxicillin": 30,
}