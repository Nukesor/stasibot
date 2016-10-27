import picamera
import telegram
from gpiozero import MotionSensor
from time import sleep

TOKEN = 'asdfapoihawef'


class SecurityBot():
    def __init__(self):
        self.running = True
        self.movement = False
        self.last_movement = None
        self.sensor = MotionSensor(4)
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240)
        self.camera.framerate = 24

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

    def main(self):
        while True:
            if self.sensor.motion_detected:
                self.capture = True
                print("Motion detected!")

            self.check_telegram()

            sleep(1)
