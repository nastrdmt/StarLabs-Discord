import os
import sys
from colorama import init
from pyfiglet import figlet_format
from termcolor import cprint


def show_logo():
    os.system("cls")
    init(strip=not sys.stdout.isatty())
    print("\n")
    logo = figlet_format("STAR LABS", font="banner3")
    cprint(logo, 'light_cyan')
    print("")


MENU_ITEMS = [
    "Inviter",
    "Press Button",
    "Press Reaction",
    "Change Name",
    "Change Username",
    "Change Password",
    "Change Profile Picture",
    "Send message to the channel",
]

CAPTCHA_BOTS = [
    "Nothing",
    "Pandez",
    "CaptchaBot",
    "Sledgehammer",
    "Enter Form"
]
