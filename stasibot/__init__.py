#!/bin/env python3
import argparse
from stasibot.stasibot import SecurityBot


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='stasibot')

    args = parser.parse_args()

    bot = SecurityBot(args)
    try:
        bot.send_message('Bot started.')
        bot.main()
    except KeyboardInterrupt:
        print('KeyboardInterrupt. Stopping.')
        pass
