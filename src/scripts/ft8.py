# Documentation is like sex.
# When it's good, it's very good.
# When it's bad, it's better than nothing.
# When it lies to you, it may be a while before you realize something's wrong.
import time

if __name__ == '__main__':
    import sys
    sys.path.append("D:/Lesko/workspace/ham/Yaesu991aCAT/src")

from ft991a import Ft991a
import argparse


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

__VERSION__ = "1.0.0"

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
                        "SH020"]


def read_original_settings(ser, save_file="original.dat"):
    print("Reading original settings ...")
    with open(save_file, "w") as original_file:
        for ms in read_menu_settings:
            print(ser.debug_send(f"EX{ms:0>3};"))
            s = ser.debug_send(f"EX{ms:0>3};")
            original_file.write(f"{s}\n")

        for os in read_other_settings:
            print(ser.debug_send(os))
            original_file.write(f"{ser.debug_send(os)}\n")
    print("Reading original settings ... DONE")


def to_ft8(ser):
    print("Configuring FT8 ...")
    for ms, param in write_menu_settings:
        s = f"EX{ms:0>3}{param};"
        print(s)
        ser.debug_send(s)

    for os in write_other_settings:
        print(os)
        ser.debug_send(os)
    print("Configuring FT8 ... DONE")


def restore_original(ser, restore_file="original.dat"):
    print("Restoring original settings ...")
    with open(restore_file, "r") as original_file:
        commands = original_file.read().split("\n")
        for command in commands:
            print(command)
            ser.debug_send(command)
    print("Restoring original settings ... DONE")


def main():
    parser = argparse.ArgumentParser(description=f"Set Yaesu FT-991A for FT8. You can also save configuration "
                                                 f"before and restore it after you are done with FT8."
                                                 f"Version {__VERSION__}")
    parser.add_argument("com_port", help="COM port on which FT991A is connected", type=str)
    parser.add_argument("action", choices=["save", "ft8", "restore"], help="r: read and save, ft8: configure for FT8, "
                                                                           "o: restore original")
    parser.add_argument("-b", "--baud", type=int, default=38400, help="Set baud rate - defaults to 38400")
    parser.add_argument("-f", "--file", type=str, default="original.dat", help="File to save to or read from - "
                                                                               "defaults to 'origimal.dat'")
    parser.add_argument("-p", "--power", type=str, default=50, help="Output power level to set - defaults to 50W")
    args = parser.parse_args()

    ft = Ft991a(args.com_port, args.baud)
    ft.open_serial()

    if args.action == "save":
        read_original_settings(ft, save_file=args.file)
    elif args.action == "ft8":
        to_ft8(ft)
        time.sleep(1)
        ft.set_vfo("14.073M", "A")
        ft.antenna_tuner_ctrl("TUNE", wait_complete=True)
        ft.set_vfo("14.074M", "A")
        ft.debug_send(f"PC{args.power:0>3};")
    elif args.action == "restore":
        restore_original(ft, restore_file=args.file)

    ft.close_serial()


if __name__ == "__main__":
    main()
