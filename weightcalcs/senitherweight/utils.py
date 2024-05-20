import aiohttp

from senitherweight.constants import skill_max_level


def get_skill_lvl(skill_type: str, exp: int):
    max_level = skill_max_level[skill_type]
    levels = {
        "0": 0, "1": 50, "2": 175, "3": 375, "4": 675, "5": 1175, "6": 1925, "7": 2925, "8": 4425, "9": 6425,
        "10": 9925, "11": 14925, "12": 22425, "13": 32425, "14": 47425, "15": 67425, "16": 97425, "17": 147425,
        "18": 222425, "19": 322425, "20": 522425, "21": 822425, "22": 1222425, "23": 1722425, "24": 2322425,
        "25": 3022425, "26": 3822425, "27": 4722425, "28": 5722425, "29": 6822425, "30": 8022425, "31": 9322425,
        "32": 10722425, "33": 12222425, "34": 13822425, "35": 15522425, "36": 17322425, "37": 19222425,
        "38": 21222425, "39": 23322425, "40": 25522425, "41": 27822425, "42": 30222425, "43": 32722425,
        "44": 35322425, "45": 38072425, "46": 40972425, "47": 44072425, "48": 47472425, "49": 51172425,
        "50": 55172425, "51": 59472425, "52": 64072425, "53": 68972425, "54": 74172425, "55": 79672425,
        "56": 85472425, "57": 91572425, "58": 97972425, "59": 104672425, "60": 111672425
    }
    for level in levels:
        if exp >= levels[str(max_level)]:
            return max_level
        if levels[level] > exp:
            lowexp = levels[str(int(level) - 1)]
            highexp = levels[level]
            difference = highexp - lowexp
            extra = exp - lowexp
            percentage = (extra / difference)
            return (int(level) - 1) + percentage


def get_cata_lvl(exp: int):
    levels = {
        '1': 50, '2': 125, '3': 235, '4': 395, '5': 625, '6': 955, '7': 1425, '8': 2095, '9': 3045,
        '10': 4385, '11': 6275, '12': 8940, '13': 12700, '14': 17960, '15': 25340, '16': 35640,
        '17': 50040, '18': 70040, '19': 97640, '20': 135640, '21': 188140, '22': 259640, '23': 356640,
        '24': 488640, '25': 668640, '26': 911640, '27': 1239640, '28': 1684640, '29': 2284640,
        '30': 3084640, '31': 4149640, '32': 5559640, '33': 7459640, '34': 9959640, '35': 13259640,
        '36': 17559640, '37': 23159640, '38': 30359640, '39': 39559640, '40': 51559640, '41': 66559640,
        '42': 85559640, '43': 109559640, '44': 139559640, '45': 177559640, '46': 225559640,
        '47': 285559640, '48': 360559640, '49': 453559640, '50': 569809640
    }
    for level in levels:
        if exp >= levels["50"]:
            return 50
        if levels[level] > exp:
            if int(level) == 1:
                level = str(2)
            lowexp = levels[str(int(level) - 1)]
            highexp = levels[level]
            difference = highexp - lowexp
            extra = exp - lowexp
            percentage = (extra / difference)
            return (int(level) - 1) + percentage


async def get_profile(uuid: str, api_key: str, session: aiohttp.ClientSession, cute_name: str = None) -> dict:
    async with session.get("https://api.hypixel.net/skyblock/profiles", params={
        "key": api_key,
        "uuid": uuid
    }) as r:
        response_json = await r.json()

        if cute_name:
            try:
                return [
                    profile for profile in response_json.get("profiles", []) if profile["cute_name"] == cute_name
                ][0]["members"][uuid]
            except IndexError:
                raise ValueError(f"Could not find profile with cute name {cute_name}")
        # select the profile where selected is true
        for profile in response_json.get("profiles", []):
            if profile["selected"]:
                return profile["members"][uuid]


async def get_player(uuid: str, api_key: str, session: aiohttp.ClientSession):
    async with session.get("https://api.hypixel.net/player", params={
        "key": api_key,
        "uuid": uuid
    }) as r:
        return (await r.json())["player"]


async def get_uuid(username: str, session: aiohttp.ClientSession):
    async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as r:
        return (await r.json())["id"]


async def get_username(uuid: str, session: aiohttp.ClientSession):
    async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{uuid}") as r:
        return (await r.json())[-1]["name"]
