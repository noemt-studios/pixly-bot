import random

def get_footer(dev: str = "nom"):
    footers = [
        f"Need help? /help | Made by {dev}",
        f"Link your account! /link | Made by {dev}",
    ]

    return random.choice(footers)


