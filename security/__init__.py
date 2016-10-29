#!/bin/env python3
import argparse
from security.security_bot import SecurityBot


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='secucam')

    args = parser.parse_args()

    bot = SecurityBot(args)
    bot.main()
