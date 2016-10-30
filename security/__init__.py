#!/bin/env python3
import argparse
from security.security_bot import SecurityBot


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='stasibot')

    args = parser.parse_args()

    bot = SecurityBot(args)
    try:
        bot.main()
    except KeyboardInterrupt:
        print('KeyboardInterrupt. Stopping.')
        pass
