# Documentation is like sex.
# When it's good, it's very good.
# When it's bad, it's better than nothing.
# When it lies to you, it may be a while before you realize something's wrong.
import re
import time
from collections import namedtuple
from typing import Optional, Union
import serial

from ft991a_config import Ft991aConfig
from menu import Menu


COMMANDS_CSV = "commands.csv"
DEBUG = False


def parse_raw_command_data():
    hm_file = "archive/hm.txt"
    with open(hm_file, "r") as hmf:
        data = hmf.read()

    data = data.split("\n")

    with open(COMMANDS_CSV, "w") as cof:
        cof.write("command, description, set, read, answer\n")
        for line in data:
            command, description, _set, _read, _answer, _ = line.split("\t")

            _set = 1 if _set == "O" else 0
            _read = 1 if _read == "O" else 0
            _answer = 1 if _answer == "O" else 0

            s = f"{command.upper()}, {description.title()}, {_set}, {_read}, {_answer}\n"
            print(s)
            cof.write(s)


class CommandError(Exception):
    pass


class ParameterError(Exception):
    pass


class Ft991aCommand:
    TERMINATOR = ";"

    def __init__(self, command: str, 
                 description: Optional[str] = None, 
                 allow_set: bool = False, 
                 allow_read: bool = False, 
                 allow_answer: bool = False):
        command = command.upper()
        self.__check_command(command)
        self.command = command

        self.description = description
        self.allow_set = allow_set
        self.allow_read = allow_read
        self.allow_answer = allow_answer

    @staticmethod
    def __check_command(command):
        if len(command) != 2:
            raise CommandError(f"Length of command '{command}' is not 2.")

    @staticmethod
    def __check_parameter(parameter):
        if not isinstance(parameter, (str, int)):
            raise ParameterError(f"Parameter type({repr(parameter)}) must be <str>.")

    def get(self, parameter: Optional[Union[str, int]] = None):
        if parameter is not None:
            self.__check_parameter(parameter)
            return f"{self.command}{parameter}{self.TERMINATOR}"
        return f"{self.command}{self.TERMINATOR}"

    def __repr__(self):
        return f"<{self.command} {self.description}> <allow_set: {self.allow_set}>" \
               f" <allow_read: {self.allow_read}> <allow_answer: {self.allow_answer}>"


def load_commands_to_objects():
    with open(r"D:\Lesko\workspace\ham\Yaesu991aCAT\src\commands.csv", "r") as cf:
        data = cf.read()

    data = data.split("\n")
    out = {}
    for line in data[1:]:
        line = line.split(",")
        out[line[0]] = Ft991aCommand(*line)
    return out


class CommandNotFoundError(Exception):
    pass


class ParseFrequencyError(Exception):
    pass


class ActionNotSupportedError(Exception):
    pass


class MalformedResponse(Exception):
    pass


class Ft991a:
    COMMANDS = load_commands_to_objects()

    def __init__(self, serial_port, baud_rate):
        self.serial_port = serial_port
        self.baud_rate = baud_rate

        self.function_menu = Menu()

        self.ser: Optional[serial.Serial] = None

    def open_serial(self):
        print(f"Opening serial <{self.serial_port} {self.baud_rate}>")
        self.ser = serial.Serial(self.serial_port, self.baud_rate)
        if not self.ser.is_open:
            self.ser.open()

    def close_serial(self):
        if self.ser.is_open:
            self.ser.close()

    def __ser_send(self, command, raw=False):
        self.ser.reset_input_buffer()
        self.ser.write(command.encode("utf-8"))
        self.ser.flush()

        time.sleep(0.1)
        if self.ser.in_waiting:
            recv_str = self.ser.read(self.ser.in_waiting).decode("utf-8")
            # Read answer if it was returned
            m = re.search(fr"^{command[:2]}([\d+\-A-Za-z ]*);", recv_str)
            if m:
                if raw:
                    return m.group(0)
                return m.group(1)
            # Check for error
            else:
                m = re.match(r"^\?;", recv_str)
            if m:
                raise MalformedResponse(f"Command '{command}' returned error '{recv_str}'.")
            else:
                raise MalformedResponse(f"Command '{command}' returned unknown response '{recv_str}'.")
        # Command without answer
        else:
            return None

    def debug_send(self, command):
        return self.__ser_send(command, raw=True)

    def __get_command(self, command):
        if command in self.COMMANDS:
            return self.COMMANDS[command]
        raise CommandNotFoundError(f"Command '{command}' not supported.")

    def __send_command(self, command, parameter=None):
        return self.__ser_send(self.__get_command(command).get(parameter))

    @staticmethod
    def __parse_frequency(freq: Union[str, int]) -> str:

        suffixes = Ft991aConfig.frequency_suffixes
        if isinstance(freq, str):
            suffix = freq[-1]
            if suffix in suffixes:
                s = f"{int(float(freq[:-1]) * suffixes[suffix]):0>9}"
                if len(s) > 9:
                    raise ParseFrequencyError("Maximum supported freq exceeded.")
                return s
            else:
                raise ParseFrequencyError(f"No unit suffix '{suffix}'.")
        elif isinstance(freq, int):
            # Assume Hz
            s = f"{freq:0>9}"
            if len(s) > 9:
                raise ParseFrequencyError("Maximum supported freq exceeded.")
            return s
        else:
            raise ParseFrequencyError("Frequency must be string.")

    def vfoa_to_vfob(self):
        """Copies VFO-B frequency and data to VFO-A.

        "A=B" button on the front panel.

        :return: None
        """
        return self.__send_command("AB")

    def vfob_to_vfoa(self):
        """Copies VFO-A frequency and data to VFO-B.

        :return: None
        """
        return self.__send_command("BA")

    def antenna_tuner_ctrl(self, action: str, **kwargs):
        """Control of on-board antenna tuner.

        "TUNE" button on the front panel.

        :param action: "ON" ..... turn tuner on
                       "OFF" .... turn tuner off
                       "TUNE" ... start tuning
        :keyword wait_complete: only for TUNE. Waits for tune process to complete
        :return: None
        """
        actions = Ft991aConfig.antenna_tuner_actions
        action = action.upper()
        if action not in actions:
            raise ActionNotSupportedError(f"Action '{action}' is not supported with 'AC' command.")
        if action == "TUNE":
            ans = self.__send_command("AC", f"00{actions[action]}")
            if kwargs.get("wait_complete", False):
                while self.read_antenna_tuner().tune:
                    time.sleep(0.5)

            return ans

    def read_antenna_tuner(self):
        """Read status of on-board antenna tuner.

        :return: namedtuple [on: bool ..... tuner on
                             tune: bool ... tune process active]
        """
        AntennaTunerAnswer = namedtuple("AntennaTunerAnswer", "on tune")
        ans = self.__send_command("AC")
        ans = AntennaTunerAnswer(on=True if ans[-1] == "1" else False, 
                                 tune=True if ans[-1] == "2" else False)
        return ans

    def set_af_gain(self, gain: int):
        """Set AF (audio) gain. Sets the receiver audio volume level.

        :param gain: between 0 and 255
        """
        if gain < 0 < 256:
            raise ParameterError(f"Gain can be between 0 and 255, not '{gain}'.")
        self.__send_command("AG", f"0{gain:0>3}")

    def read_af_gain(self) -> int:
        """Read current AF (audio) gain setting.

        :return: AF gain
        """
        return int(self.__send_command("AG", parameter="0"))

    # TODO: implement "AI  -  auto information"

    # TODO: implement "AM  -  VFO-A to memory chanel"

    def set_auto_notch(self, on: bool):
        """DNF - Digital Notch Filter.
        When multiple interfering carriers are encountered during reception,
        the DNF can significantly reduce the level of these signals.

        "F -> DNF" option in function menu.

        :param on: turn auto-notch on or off
        :return: None
        """
        state = 1 if on else 0
        return self.__send_command("BC", parameter=f"0{state}")

    def read_auto_notch_on(self) -> bool:
        """Read current state of auto-notch (DNF).

        :return: state of auto-notch
        """
        return bool(int(self.__send_command("BC", parameter="0")[-1]))

    def band_down(self):
        """One band down.

        :return: None
        """
        return self.__send_command("BD", parameter="0")

    def band_up(self):
        """One band up.

        :return: None
        """
        return self.__send_command("BU", parameter="0")

    def set_break_in(self, on):
        """Automatic activation of the transmitter when CW key is closed.

        "F -> BK-IN" option in function menu.

        :param on: turn break-in on or off
        :return:
        """
        state = 1 if on else 0
        return self.__send_command("BI", parameter=f"{state}")

    def is_break_in_on(self) -> bool:
        """Read current state of break-in.

        :return: state of auto-notch
        """
        return bool(int(self.__send_command("BI")[-1]))

    def set_manual_notch_state(self, on: bool):
        """NOTCH

        :param on: turn manual-notch on or off
        :return: None
        """
        state = 1 if on else 0
        return self.__send_command("BP", parameter=f"00{state}")

    def set_manual_notch_level(self, level: int):
        """Set manual-notch level.

        :param level: frequency in hertz. Must be between 1Hz and 3200Hz.
        :return: None
        """
        if 1 > level > 3200:
            raise ParameterError(f"Manual-notch level can be between 0 and 3200, not '{level}'.")
        level = level // 10
        return self.__send_command("BP", parameter=f"01{level:0>3}")

    def read_manual_notch_level(self) -> int:
        """Read manual-notch frequency.

        :return: manual-notch frequency in Hz
        """
        ans = self.__send_command("BP", parameter="01")
        return int(ans[-3:]) * 10

    def is_manual_notch_on(self) -> bool:
        """Read current state of manual-notch.

        :return: state of manual-notch
        """
        return bool(int(self.__send_command("BP", parameter="00")[-1]))

    def set_band(self, band):
        """Set band.

        :param band:
        :return:
        """
        bands = Ft991aConfig.bands

        if isinstance(band, int):
            if band in bands:
                band_num = band
            else:
                raise ParameterError(f"No band entry for '{band}'")
        elif isinstance(band, str):
            for _band, name in bands.items():
                if band in name:
                    band_num = _band
                    break
            else:
                raise ParameterError(f"No band entry for '{band}'")
        else:
            raise ParameterError("Band must be int or str.")
        return self.__send_command("BS", parameter=f"{band_num:0>2}")

    def read_menu_function(self, num):
        command = "EX"
        param = self.function_menu.get_menu_function(num).read_command()
        return self.__send_command(command, parameter=param)

    def write_menu_function(self, num, param):
        command = "EX"
        param = self.function_menu.get_menu_function(num).format_param(param)
        return self.__send_command(command, parameter=param)

    def is_rx_busy(self) -> bool:
        """IS RX busy (is squelch opened)?

        :return: state of rx-busy (squelch)
        """
        return bool(int(self.__send_command("BY", )[-2]))

    def set_vfo(self, frequency, ab: str = "A"):
        """Set frequency for VFO-A or VFO-B.
           Suffix must be supplied and must be one of the following:
           [M .... mega
            k ... kilo]

            e.g.:
            "14.25M"
            "3500k"

        :param frequency: string of frequency value
        :param ab: "A" ... "VFO-A"
                   "B" ... "VFO-B"
        :return: None
        """
        command = "FA" if ab == "A" else "FB"
        return self.__send_command(command, self.__parse_frequency(frequency))

    def read_vfo(self, ab: str = "A") -> int:
        """Read currently set VFO-A or VFO-B frequency.

        :param ab: "A" ... "VFO-A"
                   "B" ... "VFO-B"
        :return: frequency in hertz
        """
        command = "FA" if ab == "A" else "FB"
        return int(self.__send_command(command))

    def write_memory_channel(self, channel: int, frequency: str, mode: str, tag: str = " "*12, clar_offset: int = 0,
                             rx_clar=False, tx_clar=False, ctcss=False, operation_mode="simplex"):
        """Save to internal memory.

        :param channel: memory channel to which to save, between 0 - 117
        :param frequency: frequency to save
        :param mode: modulation (LSB, USB, CW, FM, AM, RTTY-LSB, CW-R, DATA-LSB,
                                RTTY-USB, DATA-FM, FM-N, DATA-USB, AM-N, C4FM)
        :param tag: characters (up to 12 ASCII)
        :param clar_offset: clarifier offset. 0000 - 9999
        :param rx_clar: rx-clar on/off
        :param tx_clar: tx clar on/off
        :param ctcss: CTCSS status (OFF=False, CTCSS ENC/DEC, CTCSS ENC)
        :param operation_mode: operational mode [simplex, plus shift, minus shift]
        """

        # TODO: implement checks for inputs

        frequency = self.__parse_frequency(frequency)
        clar_offset_dir = "+" if clar_offset >= 0 else "-"
        rx_clar = "1" if rx_clar else "0"
        tx_clar = "1" if tx_clar else "0"
        mode = Ft991aConfig.r_modes[mode]
        ctcss = Ft991aConfig.r_ctcss_states[ctcss]
        operation_mode = Ft991aConfig.r_operation_modes[operation_mode]

        #        P1           P2                            P3            P4        P5     P6   P7  P8  P9      P10
        s = f"{channel:0>3}{frequency}{clar_offset_dir}{clar_offset:0>4}{rx_clar}{tx_clar}{mode}0{ctcss}00{operation_mode}0{tag: <12}"
        self.__send_command("MT", parameter=s)

    def read_memory_channel(self, channel: int, raw=False):
        """Read currently saved settings for given channel.

        :param channel: channel, between 0 - 117
        :param raw: if true it will return data in a form
                    ready to be written back into memory with self.write_memory_channel(**)
        :return: namedtuple ChannelInfo [channel: int .......... 0 - 117
                                         frequency: int ........ frequency in Hz
                                         clar_offset: int ...... 0 - 9999 Hz
                                         rx_clar: bool ......... state, on/off]
                                         tx_clar: bool ......... state, on/off
                                         mode: str ............. mode as LSB, USB, FM, ...
                                         memory_mode: .......... memory smth ...
                                         ctcss: bool/str ....... off/'CTCSS ENC/DEC'/'CTCSS ENC'
                                         operation_mode: str ... simplex or +/-
                                         tag: str .............. tag up to 12 characters long (ASCII)]
        :return: dict refer to raw parameter documentation
        """
        ChannelInfo = namedtuple("ChannelInfo",
                                 "channel frequency clar_offset rx_clar tx_clar "
                                 "mode memory_mode ctcss operation_mode tag")
        try:
            ans = self.__send_command("MT", parameter=f"{channel:0>3}")
        except MalformedResponse:
            return ChannelInfo(*[None]*10)

        ch_info = ChannelInfo(
            channel=channel,
            frequency=int(ans[3:12]),
            clar_offset=int(ans[12:17]), 
            rx_clar=True if ans[17] == "1" else False, 
            tx_clar=True if ans[18] == "1" else False, 
            mode=Ft991aConfig.modes[ans[19]],
            memory_mode=Ft991aConfig.memory_mode[ans[20]],
            ctcss=Ft991aConfig.ctcss_states[ans[21]],
            operation_mode=Ft991aConfig.operation_modes[ans[24]],
            tag=ans[-12:].strip()
        )
        if raw:
            write_fields = ("channel", "frequency", "mode", "tag", "clar_offset",
                            "rx_clar", "tx_clar", "ctcss", "operation_mode")
            return {field: ch_info.__getattribute__(field) for field in ch_info._fields if field in write_fields}
        return ch_info

    def power_on(self):
        """Power transceiver on.

        :return: None
        """
        time_between_dummy = Ft991aConfig.time_between_dummy
        if time_between_dummy < 1.1:
            raise ValueError(f"time_beetween_dummy must be at least 1.1s not {time_between_dummy}s.")
        self.__ser_send("DD;")  # Dummy command
        time.sleep(time_between_dummy)
        return self.__send_command("PS", parameter="1")

    def power_off(self):
        """Power transceiver off.

        :return: None
        """
        return self.__send_command("PS", parameter="0")

    def read_smeter(self) -> int:
        """Read current S-meter reading.

        :return: S-meter reading, between 0 - 255
        """
        return int(self.__send_command("SM", parameter="0"))

    def set_squelch_level(self, squelch: int):
        """Set squelch level.

        :param squelch: squelch to set, between 0 - 100
        :return: None
        """
        if squelch < 0 or squelch > 100:
            raise ParameterError(f"Squelch level can be between 0 and 100, not '{squelch}'.")
        return self.__send_command("SQ", parameter=f"0{squelch:0>3}")

    def read_squelch(self) -> int:
        """Read currently set squelch level.

        :return: squelch level.
        """
        return int(self.__send_command("SQ", parameter="0"))

    def read_tx_state(self) -> str:
        """Read current TX status.

        :return: "ON" .......... TX is on
                 "OFF" ......... TX is off
                 "RADIO_ON" .... TX is on via PTT
        """
        return Ft991aConfig.tx_state[self.__send_command("TX")]

    def tx_on(self):
        """TX on - start transmitting.

        :return: None
        """
        return self.__send_command("TX", parameter="1")

    def tx_off(self):
        """TX off - stop transmitting.

        :return: None
        """
        return self.__send_command("TX", parameter="0")

    def list_menu_settings(self):
        for opt in range(1, 154):
            s = f"EX{opt:0>3};"
            print(s, end=" - ")
            ans = self.debug_send(s)
            print(ans)

    def list_memory(self):
        for ch in range(1, 118):
            print(self.read_memory_channel(ch, raw=True))


if __name__ == '__main__':
    ft = Ft991a("COM3", 38400)
    ft.open_serial()


    def write_repeaters_to_memory():
        ft.write_memory_channel(1, frequency="145.6875M", mode="FM", operation_mode="-", tag="Zagarski vrh")  # Zagarski vrh S55VZV
        ft.write_memory_channel(2, frequency="145.775M", mode="FM", operation_mode="-", tag="Krim S55VLJ")  # Krim S55VLJ
        ft.write_memory_channel(3, frequency="145.6125M", mode="FM", operation_mode="-", tag="Mohor S55VKR")  # Mohor S55VKR
        ft.write_memory_channel(4, frequency="145.7875M", mode="FM", operation_mode="-", tag="Mozirje")  # Spodnje Krase (Mozirje) S55VMO
        ft.write_memory_channel(5, frequency="145.650M", mode="FM", operation_mode="-", tag="Kup S55VBG")  # Kup (Podbrdo) S55VBG
        ft.write_memory_channel(6, frequency="145.625M", mode="FM", operation_mode="-", tag="Nanos S55VKP")  # Nanos S55VKP
        ft.write_memory_channel(7, frequency="145.725M", mode="FM", operation_mode="-", tag="Vojsko")  # Vojsko S55VID
        ft.write_memory_channel(8, frequency="145.700M", mode="FM", operation_mode="-", tag="Mrzlica")  # Mrzlica S55VCE

        ft.write_memory_channel(20, frequency="145.550M", mode="FM", tag="CQ FM SOTA")
        ft.write_memory_channel(21, frequency="144.300M", mode="USB", tag="CQ SSB")
        ft.write_memory_channel(22, frequency="145.325M", mode="FM", tag="V26 S51SLO")

    def save_current_settings():
        s_t = time.time()
        all_settings = []
        for _, command in ft.COMMANDS.items():
            if command.allow_set == "1" and command.allow_read == "1":
                suffix = ""
                if command.command in "AG BC CT GT IS NA NB NL NR OS PA RA RG RL SH SM SQ".split(" "):
                    suffix = "0"
                elif command.command == "EX":
                    print("Menu...")
                    for item in range(1, 154):
                        s = f"EX{item:0>3};"
                        ans = ft.debug_send(s)
                        all_settings.append(ans)
                    continue
                if command.command in "BP CN CO DT KM LM MD ML MR MT OI PB PR RI RM".split(" "):
                    print(f"Skipping command {command} ...")
                    continue
                s = f"{command.command}{suffix};"
                ans = ft.debug_send(s)
                all_settings.append(ans)
        print("Memory...")
        for item in range(1, 118):
            s = f"MT{item:0>3};"
            try:
                ans = ft.debug_send(s)
            except MalformedResponse:
                continue
            all_settings.append(ans)

        tit = time.time() - s_t
        print(f"It took {tit}sec to read {len(all_settings)} settings, that is {len(all_settings)/tit} settings/sec")
        print(all_settings)

        with open("last_settings.dat", "w") as s_file:
            for setting in all_settings:
                s_file.write(f"{setting}\n")


    def load_settings_dat(dat_name):
        with open(dat_name, "r") as dat_file:
            all_settings = dat_file.read()
        all_settings = all_settings.split("\n")
        for setting in all_settings:
            if setting in "EX0313; EX087G0O4Y; FT0; PS;".split(" "):
                print(f"Skipping {setting}")
                continue
            try:
                ft.debug_send(setting)
            except MalformedResponse as err:
                print(f"Error {setting} - {err}")




    # save_current_settings()
    # load_settings_dat("last_settings.dat")

    # print(ft.read_menu_function(13))
    # ft.write_menu_function(13, 1)
    # print(ft.read_menu_function(13))
    # ft.write_menu_function(13, 0)
    # print(ft.read_menu_function(13))

    ft.close_serial()
