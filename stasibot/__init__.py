#!/bin/env python3
import argparse
import time
import RPi.GPIO as gpio
from stasibot.stasibot import SecurityBot


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='stasibot')

    args = parser.parse_args()

    bot = SecurityBot(args)
    try:
        bot.send_message('Bot starting up.')
        # Documentation says that sensor module needs about
        # 1 Minute to power up and fires a few times during powering up
        time.sleep(60)
        bot.send_message('Bot started up.')
        bot.main()
    except KeyboardInterrupt:
        print('KeyboardInterrupt. Stopping.')
        pass
    except Exception as e:
        gpio.cleanup()
        print('Some other error occured.')
        print(e)
