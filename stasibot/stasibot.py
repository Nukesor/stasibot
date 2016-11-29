import os
import picamera
import telegram
import subprocess
import RPi.GPIO as gpio
from collections import deque
from datetime import datetime, timedelta
from stasibot.config import (
    CHANNEL,
    NAME,
    TARGET_FOLDER,
    TEMP_FOLDER,
    USERNAME,
    USER_ID,
    TELEGRAM_API_KEY,
)


class SecurityBot():
    def __init__(self, args):
        # Status of the bot
        self.running = True
        self.token = TELEGRAM_API_KEY
        self.name = NAME
        self.temp_folder = TEMP_FOLDER
        self.user_name = USERNAME
        self.user_id = USER_ID

        # Motion sensor for pi
        self.channel = CHANNEL
        gpio.setmode(gpio.BOARD)
        gpio.setup(self.channel, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        gpio.add_event_detect(self.channel, gpio.RISING)
        self.movement = False
        self.last_movement = None
        self.motion_amount = 0
        # Trigger once to get it initialized
        gpio.event_detected(self.channel)

        # Camera initialization
        self.camera = picamera.PiCamera()
        self.camera.resolution = (1920, 1080)
        self.camera.framerate = 24

        self.recording = False
        self.stop = False
        self.movie_path = None
        self.movies_for_upload = deque()
        self.record_started = None
        self.record_for_minutes = None

        # Uploader process for syncing videos to server
        self.upload = True
        self.target_folder = TARGET_FOLDER
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
            timeout=1
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
        command = command.lower()
        commands = ['start', 'stop', 'startrecording', 'stoprecording', 'upload']
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
            elif command == 'stoprecording':
                if self.recording:
                    self.stop = True
                else:
                    update.message.reply_text('Bot not recording.')
            elif basecommand == 'startrecording':
                splitted = command.split(' ')
                if len(splitted) != 2:
                    update.message.reply_text("Failed. Structure of this command"
                                              " is 'startrecording int(minutes)'.")
                else:
                    minutes = None
                    try:
                        minutes = int(splitted[1])
                    except:
                        update.message.reply_text("Failed. First parameter needs to be an int")
                    if minutes:
                        self.record_for_minutes = minutes
                        self.start_recording()
                        update.message.reply_text("Start recording for for {} minutes"
                                                  .format(minutes))

            elif basecommand == 'upload':
                splitted = command.split(' ')
                if len(splitted) != 2:
                    update.message.reply_text("Failed. Structure of this command is 'upload [0,1]'")
                else:
                    state = None
                    try:
                        state = int(splitted[1])
                        if state != 0 and state != 1:
                            update.message.reply_text("Failed. Second parameter needs to be [0,1]'")
                        else:
                            self.upload = bool(state)
                    except:
                        update.message.reply_text("Failed. First parameter needs to be an int")

        else:
            if update:
                update.message.reply_text('Valid commands are {}.'.format(commands))

    def start_recording(self):
        """Start recording to a new file."""
        if not self.recording:
            # Create directory for temporary video files
            home = os.path.expanduser('~')
            temporary_movie_folder = os.path.join(home, self.temp_folder)
            if not os.path.exists(temporary_movie_folder):
                os.makedirs(temporary_movie_folder)

            self.record_started = datetime.now()
            # Get movie name with timestamp
            if self.last_movement:
                movie_name = self.last_movement.strftime('stasibot-%Y%m%d-%H%M.h264')
            else:
                movie_name = self.record_started.strftime('stasibot-%Y%m%d-%H%M.h264')
            self.movie_path = os.path.abspath(os.path.join(temporary_movie_folder, movie_name))
            # Start recording
            self.camera.start_recording(self.movie_path)
            self.recording = True
            return True
        else:
            return True

    def stop_recording(self):
        """Stop recording and mark file for upload."""
        if self.recording:
            self.camera.stop_recording()
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
                    path = self.movies_for_upload.popleft()
                    self.send_message('Video file {} uploaded.'
                                      .format(os.path.basename(path)))
                    os.remove(path)
                    self.uploader = None
                else:
                    self.send_message('Rsync upload failed.')
                    # Upload failed. Retrying
                    self.uploader = None

        if self.upload:
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
            # Check for new telegram messages
            self.check_telegram()

            # Check for movement if the bot is active
            if self.running and gpio.event_detected(self.channel):
                # Remember the last movement
                now = datetime.now()
                if self.last_movement and now - self.last_movement <= timedelta(minutes=1):
                    self.motion_amount += 1
                else:
                    self.motion_amount = 1
                self.last_movement = now
                if self.motion_amount >= 2 and not self.recording:
                    self.send_message('Motion detected: {}'
                                      .format(self.last_movement.strftime('%d.%m.%Y %H:%M')))
                    self.start_recording()
                    self.motion_amount = 0
                elif self.recording:
                    self.motion_amount = 0
            elif not self.running:
                # This resets the event_detected status for this channel
                # Otherwise we instantly start recording after setting self.running = True
                # if there has been any movement while self.running == False.
                gpio.event_detected(self.channel)

            if self.recording:
                if self.record_for_minutes:
                    # Stop recording, after the specified amount of time.
                    delta = datetime.now() - self.record_started
                    limit = timedelta(minutes=self.record_for_minutes)
                    if delta > limit or self.stop:
                        self.stop_recording()
                        self.record_for_minutes = None
                        self.record_started = None
                        self.stop = False
                        self.send_message('Movie finished')

                elif self.last_movement:
                    # Stop recording if last movement was more than 1 min ago
                    delta = datetime.now() - self.last_movement
                    limit = timedelta(minutes=1)
                    if delta > limit or self.stop:
                        self.stop_recording()
                        self.last_movement = None
                        self.record_started = None
                        self.stop = False
                        self.send_message('Movement stopped')

            # Upload files, if there are any
            self.upload_files()
