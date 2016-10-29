#!/bin/env python3
import argparse


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='secucam')
    parser.add_argument('stuff', action='store_true', help='yo')

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(vars(args))
    else:
        print('Invalid Command. Please check -h')
