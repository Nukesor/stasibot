import os
import time
import picamera
import telegram
import subprocess
from gpiozero import MotionSensor
from datetime import datetime, timedelta

TOKEN = 'asdfapoihawef'
TARGET_FOLDER = 'guest@jarvis:'


class SecurityBot():
    def __init__(self):
        # Status of the bot
        self.running = True

        # Motion sensor for pi
        self.sensor = MotionSensor(4)
        self.movement = False
        self.last_movement = None

        # Camera initialization
        self.camera = picamera.PiCamera()
        self.camera.resolution = (1920, 1080)
        self.camera.framerate = 24

        self.recording = False
        self.movie_path = None
        self.movies_for_upload = []

        # Uploader process for syncing videos to server
        self.uploader = None

        self.telegram_bot = telegram.Bot(TOKEN)

        try:
            self.telegram_update_id = self.telegram_bot.getUpdates()[0].update_id
        except IndexError:
            self.telegram_update_id = None

    def check_telegram(self):
        updates = self.telegram_bot.getUpdates(
            offset=self.telegram_update_id,
            timeout=10
        )

        for update in updates:
            if update.message:
                command = update.message.text
                self.process_command(command, update=update)

    def process_command(self, command, update=None):
        commands = ['start', 'stop']
        if command in commands:
            if command == 'start':
                if self.running is True:
                    update.message.reply_text('Bot already observing.')
                else:
                    update.message.reply_text('Bot started to observe.')

        else:
            if update:
                update.message.reply_text('Valid commands are {}.'.format(commands))

    def start_recording(self):
        home = os.path.expanduser('~')
        temporary_movie_folder = os.join(home, 'camvideos')
        if not os.path.exists(temporary_movie_folder):
            os.makedirs(temporary_movie_folder)
        movie_name = time.strftime('secucam-%Y%m%d-%H%M')
        self.movie_path = os.path.join(temporary_movie_folder, movie_name)
        if not self.recording:
            self.camera.start_recording(self.movie_path)
            self.recording = True
            return True
        else:
            return True

    def stop_recording(self):
        if self.recording:
            self.camera.stop_recording()
            self.recording = False
            self.movies_for_upload.append(self.movie_path)
            self.movie_path = None
            return True
        else:
            return False

    def upload_files(self):
        """Upload files to a server with subprocesses."""

        if self.uploader is not None:
            self.uploader.poll()
            if self.uploader.returncode is not None:
                if self.uploader.returncode == 0:
                    # Upload successful.
                    self.movies_for_upload.remove(0)
                    self.uploader = None
                else:
                    # Upload failed. Retrying
                    self.uploader = None

        # Start new uploader with next move
        if self.uploader is None and len(self.movies_for_upload) > 0:
            path = self.movies_for_upload[0]
            command = 'rsync --partial {} {}'.format(path, TARGET_FOLDER)
            self.uploader = subprocess.Popen(
                command,
                shell=True,
            )

    def main(self):
        while True:
            # Check for movement if the bot is active
            if self.running and self.sensor.motion_detected:
                # Remember the last movement
                self.last_movement = datetime.now()
                print("Motion detected!")
                self.start_recording()

            if self.recording:
                # Stop recording if last movement more than 1 min ago
                delta = datetime.now() - self.last_movement
                if delta > timedelta(minutes=1):
                    self.stop_recording()

            time.sleep(1)
