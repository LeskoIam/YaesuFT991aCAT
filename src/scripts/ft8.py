# Documentation is like sex.
# When it's good, it's very good.
# When it's bad, it's better than nothing.
# When it lies to you, it may be a while before you realize something's wrong.
from src.ft991a import Ft991a
import time


"""
These are the MENU settings that I changed from the default values.
031 CAT RATE 4800 (or faster – just make sure the software and radio match the same CAT RATE many are using the fastest “38XXX” vale.  I use 4800 and it works fine.)

032 CAT TOT 100ms
033 CAT ENABLE
062 Data Mode  OTHERS  (NOT PSK – change to OTHERS)
064 OTHER DISP (SSB) = 1500 Hz
065 OTHER SHIFT (SSB) = 1500 Hz
066 DATA LCUT FRED = OFF
068 DATA HCUT FREQ = OFF
070 DATA IN SELECT = REAR
071 DATA PTT SELECT = RTS
072 DATA PORT SELECT = USB

Yaesu FT-991 Screen settings:

These are the settings on the main screen of the FT-991 that I adjusted.
1. MD0; MODE:  DATA-USB  (NOT USB), choose the DATA-USB setting.
SH0; WIDTH: 2400 or 3000
METER: ALC (I use an external meter to watch RF power out)
4. PC; RF PWR: 8-50w  start low and work up.
3. SH0 WIDTH: 3000
2. NA0; NAR/WIDE: W 3000
DT Gain:  6   *** IMPORTANT ***
The DT Gain defaults to 50!   This will overdrive the rigs modulator which will cause unwanted audio harmonics.  Not good.  Turn the DT Gain setting down to about 4, and start working your way back up, watching for ALC on the meter as well as the power out that you want.  As you move the DT Gain setting back up (higher), you will see your power level increase as well as ALC levels.  Find the happy medium of NO ALC showing on the meter.   Excessive ALC indication is a sign that the audio drive is too high and distortion is most likely happening.
"""

ft = Ft991a("COM3", 38400)
ft.open_serial()

read_menu_settings = [32, 33, 62, 64, 65, 66, 68, 70, 71, 72]
write_menu_settings = [(32, "1"),
                       (33, "1"),
                       (62, "1"),
                       (64, "+1500"),
                       (65, "+1500"),
                       (66, "00"),
                       (68, "00"),
                       (70, "1"),
                       (71, "1"),
                       (72, "1")]

read_other_settings = ["MD0;", "FA;", "AG0;", "NA0;", "SH0;", "PC;"]
write_other_settings = ["MD0C;", "AG0000;",
                        "NA00;",
                        "SH020", "PC008;"]

for ms in read_menu_settings:
    print(ft.debug_send(f"EX{ms:0>3};"))
    time.sleep(0.5)

for os in read_other_settings:
    print(ft.debug_send(os))
    time.sleep(0.5)


print("Setup FT8 settings")
for ms, param in write_menu_settings:
    ft.debug_send(f"EX{ms:0>3}{param};")
    time.sleep(0.5)

for os in write_other_settings:
    ft.debug_send(os)
    time.sleep(0.5)

print("Setting up FT8 done...")
time.sleep(5)

a = """
EX0321;
EX0331;
EX0621;
EX064+1500;
EX065+1500;
EX06600;
EX06800;
EX0701;
EX0711;
EX0721;
MD02;
FA014230900;
AG0000;
NA00;
SH014;
PC100;
"""

print("Restoring...")
for com in a.split("\n"):
    com = com.strip()
    if not com.endswith(";"):
        continue
    print(com)
    ft.debug_send(com)
    time.sleep(0.5)


ft.close_serial()
