#!/usr/bin/env python3
"""Osgram - OSINT tool on Instagram.

Offers an interactive shell and single-command CLI to perform intelligence
analysis on Instagram accounts using legitimate free providers.
"""
import argparse
import os
import signal
import sys

from src import artwork
from src import printcolors as pc
from src.Osintgram import Osintgram

try:
    import readline
except ImportError:
    try:
        import gnureadline as readline
    except ImportError:
        try:
            import pyreadline3 as readline
        except ImportError:
            readline = None


def printlogo():
    pc.printout(artwork.ascii_art, pc.YELLOW)
    pc.printout("\nVersion 2.1 - Osgram (Free Providers & CLI)\n\n", pc.YELLOW)
    pc.printout("Type 'list' or 'help' to show all allowed commands\n")
    pc.printout("Type 'FILE=y' to save results to '<target username>_<command>.txt' (default: disabled)\n")
    pc.printout("Type 'FILE=n' to disable saving to files\n")
    pc.printout("Type 'JSON=y' to export results to '<target username>_<command>.json' (default: disabled)\n")
    pc.printout("Type 'JSON=n' to disable exporting to JSON\n\n")


def cmdlist():
    commands_help = [
        ("FILE=y/n", "Enable/disable output in a '<target username>_<command>.txt' file"),
        ("JSON=y/n", "Enable/disable export in a '<target username>_<command>.json' file"),
        ("addrs", "Get all registered addresses from target photos (reverse-geocoded)"),
        ("cache", "Clear local request cache"),
        ("captions", "Get target's photo captions"),
        ("commentdata", "Get a list of all comments on target's posts"),
        ("comments", "Get total comments and stats of target's posts"),
        ("followers", "Get target followers list"),
        ("followings", "Get users followed by target"),
        ("fwersemail", "Get public email of target followers"),
        ("fwingsemail", "Get public email of users followed by target"),
        ("fwersnumber", "Get public phone number of target followers"),
        ("fwingsnumber", "Get public phone number of users followed by target"),
        ("hashtags", "Get hashtags used by target with frequency"),
        ("info", "Get target profile info and metadata"),
        ("likes", "Get total likes and stats of target's posts"),
        ("mediatype", "Get target's post types (photo, video, carousel)"),
        ("photodes", "Get accessibility descriptions of target's photos"),
        ("photos", "Download target's photos into output folder"),
        ("propic", "Download target's profile picture in HD"),
        ("stories", "Download target's active stories"),
        ("tagged", "Get list of users tagged by target"),
        ("target", "Switch to a new target account"),
        ("wcommented", "Get list of users who commented on target's photos"),
        ("wtagged", "Get list of users who tagged target in photos"),
        ("about", "Get target account creation & country info (if supported)"),
        ("highlights", "Get target story highlights"),
        ("posting_times", "Get target posting time heatmap & frequency"),
        ("suggested", "Get target suggested profiles (if supported)"),
        ("exit/quit", "Exit the application"),
    ]
    for cmd, desc in commands_help:
        pc.printout(f"{cmd:<16}\t")
        print(desc)


def signal_handler(sig, frame):
    pc.printout("\nGoodbye!\n", pc.RED)
    sys.exit(0)


def _quit():
    pc.printout("Goodbye!\n", pc.RED)
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Osgram - OSINT analysis tool on Instagram."
    )
    parser.add_argument("id", type=str, help="Target username")
    parser.add_argument("-C", "--cookies", help="Clear previous session cookies", action="store_true")
    parser.add_argument("-j", "--json", help="Save commands output as JSON file", action="store_true")
    parser.add_argument("-f", "--file", help="Save output in a text file", action="store_true")
    parser.add_argument("-c", "--command", help="Single command mode: execute provided command", action="store")
    parser.add_argument("-o", "--output", help="Where to store downloaded photos & reports", action="store")
    parser.add_argument("-p", "--provider", help="Data provider backend (instagrapi or mock)", action="store")

    args = parser.parse_args()

    api = Osintgram(
        target=args.id,
        is_file=args.file,
        is_json=args.json,
        is_cli=bool(args.command),
        output_dir=args.output,
        clear_cookies=args.cookies,
        provider=args.provider,
    )

    commands = {
        "list": cmdlist,
        "help": cmdlist,
        "quit": _quit,
        "exit": _quit,
        "addrs": api.get_addrs,
        "cache": api.clear_cache,
        "captions": api.get_captions,
        "commentdata": api.get_comment_data,
        "comments": api.get_total_comments,
        "followers": api.get_followers,
        "followings": api.get_followings,
        "fwersemail": api.get_fwersemail,
        "fwingsemail": api.get_fwingsemail,
        "fwersnumber": api.get_fwersnumber,
        "fwingsnumber": api.get_fwingsnumber,
        "hashtags": api.get_hashtags,
        "info": api.get_user_info,
        "likes": api.get_total_likes,
        "mediatype": api.get_media_type,
        "photodes": api.get_photo_description,
        "photos": api.get_user_photo,
        "propic": api.get_user_propic,
        "stories": api.get_user_stories,
        "tagged": api.get_people_tagged_by_user,
        "target": api.change_target,
        "wcommented": api.get_people_who_commented,
        "wtagged": api.get_people_who_tagged,
        "about": api.get_about,
        "highlights": api.get_highlights,
        "posting_times": api.get_posting_times,
        "suggested": api.get_suggested,
    }

    def completer(text, state):
        options = [i for i in commands if i.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    if readline:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer)

    if not args.command:
        printlogo()

    while True:
        if args.command:
            cmd = args.command
            _cmd = commands.get(args.command)
        else:
            signal.signal(signal.SIGINT, signal_handler)
            if readline:
                readline.parse_and_bind("tab: complete")
                readline.set_completer(completer)
            pc.printout("Run a command: ", pc.YELLOW)
            try:
                cmd = input().strip()
            except EOFError:
                _quit()

            _cmd = commands.get(cmd)

        if _cmd:
            _cmd()
        elif cmd == "FILE=y":
            api.set_write_file(True)
        elif cmd == "FILE=n":
            api.set_write_file(False)
        elif cmd == "JSON=y":
            api.set_json_dump(True)
        elif cmd == "JSON=n":
            api.set_json_dump(False)
        elif cmd == "":
            pass
        else:
            pc.printout(f"Unknown command: '{cmd}'. Type 'list' or 'help' for available commands.\n", pc.RED)

        if args.command:
            break


if __name__ == "__main__":
    main()
