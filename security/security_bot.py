import os
#import picamera
import telegram
import subprocess
from collections import deque
from gpiozero import MotionSensor
from datetime import datetime, timedelta
from security.config import TELEGRAM_API_KEY


class SecurityBot():
    def __init__(self, args):
        # Status of the bot
        self.running = True
        self.token = TELEGRAM_API_KEY
        self.name = 'NSA677Bot'
        self.target_folder = 'guest@jarvis:test'
        self.temp_folder = 'camvideos'  # relative to home directory
        self.user_name = 'Nukesor'
        self.user_id = 27755184

        # Motion sensor for pi
#        self.sensor = MotionSensor(4)
        self.movement = False
        self.last_movement = None

        # Camera initialization
#        self.camera = picamera.PiCamera()
#        self.camera.resolution = (1920, 1080)
#        self.camera.framerate = 24

        self.recording = False
        self.movie_path = None
        self.movies_for_upload = deque()
        self.record_started = None
        self.record_for_minutes = None

        # Uploader process for syncing videos to server
        self.uploader = None

        self.telegram_bot = telegram.Bot(self.token)

        try:
            self.telegram_update_id = self.telegram_bot.getUpdates()[0].update_id
        except IndexError:
            self.telegram_update_id = None

    def check_telegram(self):
        """Checks telegram for new messages."""
        updates = self.telegram_bot.getUpdates(
            offset=self.telegram_update_id,
            timeout=10
        )

        for update in updates:
            if update.message:
                self.telegram_update_id = update.update_id + 1
                command = update.message.text
                # Get user_id in case we only know the username
                if not self.user_id:
                    if update.message.from_user.username == self.user_name:
                        self.user_id = update.message.from_user.id
                # Don't respond to this command, if the message is not from the
                # wanted user.
                if self.user_id:
                    self.process_command(command, update=update)

    def process_command(self, command, update=None):
        """Interprets commands from telegram user messages."""
        commands = ['start', 'stop', 'startrecording']
        basecommand = command.split(' ')[0]
        if basecommand in commands:
            if command == 'start':
                if self.running is True:
                    update.message.reply_text('Bot already observing.')
                else:
                    self.running = True
                    update.message.reply_text('Bot started to observe.')
            elif command == 'stop':
                if self.running is False:
                    update.message.reply_text('Bot already stopped.')
                else:
                    self.running = False
                    update.message.reply_text('Bot stopped.')
            elif basecommand == 'startrecording':
                splitted = command.split(' ')
                if len(splitted) != 2:
                    update.message.reply_text("Failed. Structure of this command"
                                              " is 'startrecording int(minutes)'.")
                else:
                    try:
                        minutes = int(splitted[1])
                    except:
                        update.message.reply_text("Failed. First parameter needs to be an int")
                    self.record_for_minutes = minutes
                    self.record_started = datetime.now()
                    self.start_recording()
                    update.message.reply_text("Start recording for for {} minutes".format(minutes))

        else:
            if update:
                update.message.reply_text('Valid commands are {}.'.format(commands))

    def start_recording(self):
        """Start recording to a new file."""
        # Create directory for temporary video files
        home = os.path.expanduser('~')
        temporary_movie_folder = os.path.join(home, self.temp_folder)
        if not os.path.exists(temporary_movie_folder):
            os.makedirs(temporary_movie_folder)

        # Get movie name with timestamp
        if self.last_movement:
            movie_name = self.last_movement.strftime('secucam-%Y%m%d-%H%M')
        elif self.record_started:
            movie_name = self.record_started.strftime('secucam-%Y%m%d-%H%M')
        self.movie_path = os.path.abspath(os.path.join(temporary_movie_folder, movie_name))
        if not self.recording:
            # Start recording
            open(self.movie_path, 'a').close()
            #self.camera.start_recording(self.movie_path)
            self.recording = True
            return True
        else:
            return True

    def stop_recording(self):
        """Stop recording and mark file for upload."""
        if self.recording:
            #self.camera.stop_recording()
            self.recording = False
            self.movies_for_upload.append(self.movie_path)
            self.movie_path = None
            return True
        else:
            return False

    def send_message(self, message):
        """Send a message to the user."""
        if self.user_id:
            self.telegram_bot.sendMessage(
                self.user_id,
                text=message,
            )

    def upload_files(self):
        """Upload files to a server with subprocesses."""
        if self.uploader is not None:
            self.uploader.poll()
            if self.uploader.returncode is not None:
                if self.uploader.returncode == 0:
                    # Upload successful.
                    path = self.movies_for_upload.popleft(0)
                    self.send_message('Video file {} uploaded.'
                                      .format(os.path.basename(path)))
                    os.remove(path)
                    self.uploader = None
                else:
                    self.send_message('Rsync upload failed.')
                    # Upload failed. Retrying
                    self.uploader = None

        # Start new uploader with next move
        if self.uploader is None and len(self.movies_for_upload) > 0:
            path = self.movies_for_upload[0]
            command = 'rsync --partial {} {}'.format(path, self.target_folder)
            self.uploader = subprocess.Popen(
                command,
                shell=True,
            )

    def main(self):
        while True:
            # Check for movement if the bot is active
#            if self.running and self.sensor.motion_detected:
#                # Remember the last movement
#                self.last_movement = datetime.now()
#                self.send_message('Motion detected: {}'.format(self.last_movement.strftime('%d.%m.%Y %H:%M')))
#                self.start_recording()

            if self.recording:
                if self.record_for_minutes and self.record_started:
                    # Stop recording, after the specified amount of time.
                    delta = datetime.now() - self.record_started
                    limit = timedelta(minutes=self.record_for_minutes)
                    if delta > limit:
                        self.stop_recording()
                        self.record_for_minutes = None
                        self.record_started = None
                        self.send_message('Movie finished')

                elif self.last_movement:
                    # Stop recording if last movement was more than 1 min ago
                    delta = datetime.now() - self.last_movement
                    limit = timedelta(minutes=1)
                    if delta > limit:
                        self.stop_recording()
                        self.last_movement = None
                        self.send_message('Movement stopped')

            # Check for new telegram messages
            self.check_telegram()

            # Upload files, if there are any
            self.upload_files()
