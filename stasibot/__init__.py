#!/bin/env python3
import argparse
import RPi.GPIO as gpio
from stasibot.stasibot import SecurityBot


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='stasibot')

    args = parser.parse_args()

    bot = SecurityBot(args)
    try:
        bot.send_message('Bot started up.')
        bot.main()
    except KeyboardInterrupt:
        print('KeyboardInterrupt. Stopping.')
        pass
    except Exception as e:
        gpio.cleanup()
        print('Some other error occured.')
        print(e)
