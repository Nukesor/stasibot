#!/bin/env python3
import argparse


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='secucam')
    parser.add_argument('stuff', action='store_true', help='yo')

    # Initialze supbparser
    subparsers = parser.add_subparsers(
        title='Subcommands', description='Various client')

    # Add
    # add_Subcommand = subparsers.add_parser(
    #     'add', help='Adds a command to the queue')
    # add_Subcommand.add_argument(
    #     'command', type=str, help='The command to be added')
    # add_Subcommand.set_defaults(func=execute_add)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(vars(args))
    else:
        print('Invalid Command. Please check -h')
