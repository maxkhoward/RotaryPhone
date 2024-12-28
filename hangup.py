import RPi.GPIO as GPIO
import threading
import time

BUTTON_GPIO = 25

class HangUpThread(threading.Thread):
    def __init__(self, phone):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.phone = phone
        self.daemon = True

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def run(self):
        while True:
            if not GPIO.input(BUTTON_GPIO):
                self.phone.phone_held.clear()
                self.phone.phone_hung_up.set()
                self.phone.dial_manager.clear_sequence()
                if(self.phone.state == "off-hook"):
                    print("Hanging up")
                    threading.Thread(target=self.phone.switch_state, args=("on-hook",), daemon=True).start()
            else:
                self.phone.phone_held.set()
                self.phone.phone_hung_up.clear()
                if(self.phone.state == "on-hook"):
                    print("Picking up")
                    threading.Thread(target=self.phone.switch_state, args=("off-hook",), daemon=True).start()
            time.sleep(0.1)
