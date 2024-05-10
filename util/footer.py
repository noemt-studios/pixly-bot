import random

def get_footer(dev: str = "nom"):
    footers = [
        f"Need help? /help | Made by {dev}",
        f"Made with py-cord | Made by {dev}",
    ]

    return random.choice(footers)


