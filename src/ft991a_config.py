# Documentation is like sex.
# When it's good, it's very good.
# When it's bad, it's better than nothing.
# When it lies to you, it may be a while before you realize something's wrong.
from dataclasses import dataclass


@dataclass
class Ft991aConfig:

    # Time between dummy command and on command.
    # Must be between 1s sand 2s
    time_between_dummy = 1.1

    modes = {
        "1": "LSB",
        "2": "USB",
        "3": "CW",
        "4": "FM",
        "5": "AM",
        "6": "RTTY-LSB",
        "7": "CW-R",
        "8": "DATA-LSB",
        "9": "RTTY_USB",
        "A": "DATA-FM",
        "B": "FM-N",
        "C": "DATA-USB",
        "D": "AM-N",
        "E": "C4FM"
    }

    r_modes = {val: key for key, val in modes.items()}

    antenna_tuner_actions = {
        "ON": 1,
        "OFF": 0,
        "TUNE": 2
    }

    bands = {
        0: ("1.8", "160m"),
        1: ("3.5", "80m"),
        3: ("7", "40m"),
        4: ("10", "30m"),
        5: ("14", "20m"),
        6: ("18", "17m"),
        7: ("21", "15m"),
        8: ("24.5", "24", "12m"),
        9: ("28", "10"),
        10: ("50", "6m"),
        11: ("GEN",),
        12: ("MW",),
        14: ("AIR",),
        15: ("144", "2m"),
        16: ("430", "432", "70cm")
    }

    frequency_suffixes = {
        "k": 1e3,
        "M": 1e6
    }

    memory_mode = {
        "0": "VFO",
        "1": "memory"
    }

    ctcss_states = {
        "0": False,
        "1": "CTCSS ENC/DEC",
        "2": "CTCSS ENC"
    }

    r_ctcss_states = {val: key for key, val in ctcss_states.items()}

    operation_modes = {
        "0": "simplex",
        "1": "+",
        "2": "-",
    }

    r_operation_modes = {val: key for key, val in operation_modes.items()}

    tx_state = {
        "0": "OFF",
        "1": "ON",
        "2": "RADIO_ON"
    }

    r_tx_state = {val: key for key, val in tx_state.items()}
