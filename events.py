import subprocess
import requests
import smtplib

from config import config
#from email.message import EmailMessage
from datetime import datetime
from config import config
from multiprocessing import Process
from os.path import basename

def tts_command(text):
    if config["engine"]["tts"] == "espeak":
        return ["espeak", text]
    elif config["engine"]["tts"] == "festival":
        filename = "/tmp/phone_input.txt"
        with open(filename, "w") as f:
            f.write(text)
        return ["festival", "--tts", filename]

class Event():
    def __init__(self, phone, args):
        self.args = args
        self.phone = phone

    def get_name(self):
        return "generic event"

    def get_text(self):
        return "event"

    def run(self):
        self.phone.run_until_hangup(tts_command(self.get_text()))


class FortuneEvent(Event):
    def get_name(self):
        return "fortune"

    def get_text(self):
        res = subprocess.run(["fortune", "-s"], stdout=subprocess.PIPE)
        return res.stdout.decode("utf-8")


class DirectoryEvent(Event):
    def get_name(self):
        return "directory"

    def run(self):
        self.phone.run_many_until_hangup([["aplay", config["audiofiles"]["directory"]]])

class Restart(Event):
    def get_name(self):
        return "restart"

    def run(self):
        # Restarts a recording once started. Should only be called from the reording event
        # Stops the current recording (like a hangup) and starts a new one (maybe deletes the old one)
        pass


class OperatorEvent(Event):
    def get_name(self):
        return "operator"

    def run(self):
        loop = True
        while loop:
            now = datetime.now()
            nearest_quarter = ((now.minute // 15 + 1) * 15) % 60
            next_hour = now.hour % 12 if nearest_quarter != 0 else (now.hour + 1) % 12
            next_hour = next_hour if next_hour != 0 else 12
            text = f"In {nearest_quarter - now.minute} minutes it will be {next_hour} {nearest_quarter}"
            commands = [tts_command(text), ["aplay", "/etc/phone/sound/hold.wav"]]
            self.phone.run_many_until_hangup(commands)


#class WeatherEvent(Event):
    #def get_name(self):
        #return "weather"
#
    #def get_text(self):
        #key = config["openweathermap"]["key"]
        #lat = config["openweathermap"]["lat"]
        #lon = config["openweathermap"]["lon"]
        #location = config["openweathermap"]["location"]
        #units = config["openweathermap"]["units"]
        #onecall_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={key}&units={units}"
        #onecall = requests.get(onecall_url).json()
        #current_temp = onecall["current"]["temp"]
        #current_desc = onecall["current"]["weather"][0]["description"]
        #weather = f"In {location}, it is {current_temp} degrees with {current_desc}. "
        #high_temp = onecall["daily"][0]["temp"]["max"]
        #pop = onecall["daily"][0]["pop"] * 100
        #forecast = f"Today there is a high of {high_temp} with a {pop} percent chance of percipitation."
        #return f"{weather}{forecast}"


class RecordEvent(Event):
    def get_name(self):
        return "recorder"

    def run(self):
        self.phone.run_until_hangup(tts_command("Please record a message."))
        process = subprocess.Popen(["arecord", config["engine"]["filename"]])
        self.phone.wait_until_hung_up()
        process.terminate()
        #self._send_recording()
        return ""

class PlayEvent(Event):
    def get_name(self):
        return "play"

    def run(self):
        self.phone.run_until_hangup(["aplay", config["engine"]["filename"]])

class Affirmations(Event):
    def get_name(self):
        return "affirmations"

    def run(self):
        # change this to randomly play an affirmation file
        # self.phone.run_until_hangup(["aplay", config["engine"]["filename"]])
        pass

class Advice(Event):
    def get_name(self):
        return "advice"

    def run(self):
        # change this to play the intro, then pause, then play a random piece of advice
        # self.phone.run_until_hangup(["aplay", config["engine"]["filename"]])
        pass

#class WavEvent(Event):
    #def get_name(self):
        #return basename(self.args[0])
#
    #def run(self):
        #self.phone.run_until_hangup(["aplay", self.args[0]])
#
#class RadioEvent(Event):
    #def get_name(self):
        #return "radio"
#
    #def run(self):
        #self.phone.run_until_hangup(["cvlc", config["radio"]["url"]])
