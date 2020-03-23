# Documentation is like sex.
# When it's good, it's very good.
# When it's bad, it's better than nothing.
# When it lies to you, it may be a while before you realize something's wrong.

from ft991a import Ft991a
import time

ft = Ft991a("COM3", 38400)

ft.open_serial()

# alphabet = "ABCDEFGHIJKLMNOPQRSTUWVXYZ"
# for a in alphabet:
#     for b in alphabet:
#         s = f"{a}{b}"
#         if s[:2] in ft.COMMANDS.keys():
#             print("Skipping ", a, b)
#             continue
#
#         print(f"###### {s} ######")
#         ft.debug_send(s)
#         print("############")
#         time.sleep(0.1)

# ft.power_off()
# time.sleep(10)
# ft.power_on()
# time.sleep(5)

ft.debug_send("MC021;")
ft.set_squelch_level(15)
time.sleep(2)
print(ft.read_squelch())
ft.debug_send("MC001;")
ft.debug_send("SC1;")


# print(ft.read_smeter())
# print(ft.read_tx_state())




ft.close_serial()
