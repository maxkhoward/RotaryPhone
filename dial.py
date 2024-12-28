from datetime import datetime, timedelta
import time
import RPi.GPIO as GPIO
import threading
import events
from config import config

BUTTON_GPIO = 19
REST_TIME = 0.3 # seconds
DIAL_RESET_TIME = 5 # seconds

class DialThread(threading.Thread):
    def __init__(self, phone):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.daemon = True
        self.phone = phone

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def run(self):
        pressed = True
        rest_start = datetime.now()
        count = 0
        printed = True

        while True:
            # button is pressed when pin is LOW
            if not GPIO.input(BUTTON_GPIO):
                if not pressed:
                    count+=1
                    pressed = True
                    printed = False
            # button not pressed (or released)
            else:
                if pressed:
                    rest_start = datetime.now()
                pressed = False
            if self.dial_over(rest_start) and not printed:
                # Only add this dial to queue if we should accept numbers at this time
                if self.phone.phone_held.is_set() and not self.phone.processing_event.is_set():
                    self.phone.queue.put(count % 10) # wrap 10 to 0
                count = 0
                printed = True
            time.sleep(0.01)

    def dial_over(self, rest_start):
        # After REST_TIME seconds, assume the rotary dial stopped spinning
        return datetime.now() - rest_start > timedelta(seconds=REST_TIME)


class DialManager:
    def __init__(self, phone):
        self.sequence = []
        self.phone = phone
        self.update = datetime.now()
        self._load_sequences()

    def _load_sequences(self):
        print("loading sequences")
        def recursive_add(classname, sequence_list, sequences, args):
            key = int(sequence_list[0])
            if not sequence_list[1:]:
                sequences[key] = eval(classname)(self.phone, args)
            else:
                sequences[key] = sequences[key] if key in sequences and isinstance(sequences[key], dict) else {}
                recursive_add(classname, sequence_list[1:], sequences[key], args)

        self.sequences = {}
        for sequence in config["sequences"]:
            parts = config["sequences"][sequence].split(" ", 1)
            classname = parts[0]
            args = parts[1:]
            print(sequence, classname, args, sep="\t")
            recursive_add(classname, list(sequence), self.sequences, args)

    def dial(self, number):
        print("dialing", number)
        if datetime.now() - self.update > timedelta(seconds=DIAL_RESET_TIME):
            self.sequence = []
        self.sequence.append(number)
        match = self.match_sequence()
        print(self.sequence, match, sep="\t")
        if match is not None:
            self.sequence = []
        self.update = datetime.now()
        return match

    def match_sequence(self):
        print("matching sequence")
        def recursive_find(sequence, sequences):
            if not sequence:
                return None
            digit = sequence[0]
            if not digit in sequences:
                return None
            if isinstance(sequences[digit], dict):
                return recursive_find(sequence[1:], sequences[digit])
            return sequences[digit]
        return recursive_find(self.sequence, self.sequences)

    def clear_sequence(self):
        self.sequence = []
