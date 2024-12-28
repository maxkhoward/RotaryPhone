from dial import DialManager, DialThread
from hangup import HangUpThread
from threading import Event
from config import config

import subprocess
import os
import time
import threading

from queue import Queue

class Phone:
    __instance = None
    @staticmethod
    def get_instance():
        if Phone.__instance is None:
            Phone()
        return Phone.__instance

    def __init__(self):
        print("initializing phone")
        Phone.__instance = self
        self.state = "on-hook"
        self.queue = Queue()
        self.phone_held = Event()
        self.phone_hung_up = Event()
        self.processing_event = Event()

        # start phone as on hook
        self.phone_held.clear()
        self.phone_hung_up.set()
        self.processing_event.clear()

        self.dial_thread = DialThread(self)
        self.dial_thread.start()
        self.dial_manager = DialManager(self)

        self.hang_up_thread = HangUpThread(self)
        self.hang_up_thread.start()
        
    def switch_state(self, state):
        if (self.state != state):
            print("switching state to " + state)
            self.state = state
            if (state == "on-hook"):
                #os.system("killall aplay")
                pass
            elif (state == "off-hook"):
                print('off-hook - playing welcome message')
                #self.run_until_hangup(["aplay", "/home/max.howard/phone/audio/welcome.wav"])

                subprocess.Popen(["aplay", "/home/max.howard/phone/audio/welcome.wav"])
                print('start time delay')
                time.sleep(14)
                print('time delay over')
                subprocess.Popen(["aplay", "/home/max.howard/phone/audio/beep.wav"])
                
                recordingsFileList = os.listdir(config["audiofiles"]["recordings_directory"])
                fileCount = len(recordingsFileList)
                print('recording file: ' + str(fileCount) + '.wav')
                process = subprocess.Popen(["arecord", f'{config["audiofiles"]["recordings_directory"]}{fileCount}.wav'])
                print('recording started')
                print(f'SS phone is held: {self.phone_held.is_set()}')
                print(f'SS phone is hung up: {self.phone_hung_up.is_set()}')
                #f'Hello {name}! This is {program}'
                self.wait_until_hung_up()
                process.terminate()
                print('recording stopped')
                print(f'SS phone is held: {self.phone_held.is_set()}')
                print(f'SS phone is hung up: {self.phone_hung_up.is_set()}')
                
        
    def wait_until_answered(self, timeout=None):
        return self.phone_held.wait(timeout)

    def wait_until_hung_up(self, timeout=None):
        return self.phone_hung_up.wait(timeout)

    def process_dial(self):
        try:
            dialed = self.queue.get(block=True, timeout=0.1)
        except:
            return
        response = self.dial_manager.dial(dialed)
        # If we matched a sequence, play out event
        if response is not None:
            self.processing_event.set()
            response.run()

    def clear_event(self):
        self.processing_event.clear()

    def run_until_hangup(self, command):
        print("running command until hangup")
        process = subprocess.Popen(command)
        while process.poll() is None:
            if self.wait_until_hung_up(0.1):
                print("terminating process")
                process.terminate()
                process.kill()
                return False
        return True

    def run_many_until_hangup(self, commands):
        print("running many commands until hangup")
        for command in commands:
            if not self.run_until_hangup(command):
                break
