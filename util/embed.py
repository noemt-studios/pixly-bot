import discord
from numerize.numerize import numerize
from .formatting import count

def get_embed(text, bot):
    embed = discord.Embed(
        description=text,
        color=discord.Color.blue()
    ).set_author(name=bot.user.name, icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    return embed

def generate_embed_networth_field(items, total_value, name, emoji, emojis, item_emojis):
    items = sorted(items, key=lambda x: x["price"], reverse=True)
    items_string = ""
    for item in enumerate(items):
        if item[0] == 5:
            items_string += f"... **{len(items) - 5} more**"
            break

        super_suffix = None
        suffix = ""
        for calc in item[1]["calculation"]:
            if calc["id"] == "RECOMBOBULATOR_3000":
                suffix += " "+emojis.recombobulator_3000

        if item[1]["id"].startswith("starred_"):
            item[1]["id"] = item[1]["id"][8:]

        item_emoji = item_emojis.get(item[1]["id"].upper())
        if item[1].get("type"):
            if item[1].get("skin") is None:
                item_emoji = item_emojis.get("PET_"+item[1]["type"].upper())

            else:
                item_emoji = item_emojis.get("PET_SKIN_"+item[1].get("skin").upper())

            if item[1].get("heldItem"):
                supersuffix_emoji = item_emojis.get(item[1].get("heldItem").upper())
                emoji_url = supersuffix_emoji["url"]
                emoji_id = supersuffix_emoji["id"]
                emoji_name = supersuffix_emoji["name"]

                if ".gif" in emoji_url:
                    emoji_prefix = "<a:"
                
                else:
                    emoji_prefix = "<:"

                held_item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"
                super_suffix = f"{held_item_emoji}"


        if item_emoji:
            emoji_url = item_emoji["url"]
            emoji_id = item_emoji["id"]
            emoji_name = item_emoji["name"]

            if ".gif" in emoji_url:
                emoji_prefix = "<a:"
            
            else:
                emoji_prefix = "<:"

            item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}> "

        else:
            if "new_year_cake" in item[1]["id"].lower() and "bag" not in item[1]["id"].lower():
                item_emoji_data = item_emojis.get("NEW_YEAR_CAKE")
                emoji_id = item_emoji_data["id"]
                emoji_name = item_emoji_data["name"]
                item_emoji = f"<:{emoji_name}:{emoji_id}> "

            elif "_skinned_" in item[1]["id"]:
                item_emoji_name = item[1]["id"].split("_skinned_")[1]
                item_emoji = item_emojis.get(item_emoji_name.upper())
                if item_emoji:
                    emoji_url = item_emoji["url"]
                    emoji_id = item_emoji["id"]
                    emoji_name = item_emoji["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}> "
                
                else:
                    print(item[1]["id"])
                    item_emoji = ""

            elif item[1]["id"].endswith("_shiny"):
                item_emoji_name = item[1]["id"][:-6]
                item_emoji = item_emojis.get(item_emoji_name.upper())
                if item_emoji:
                    emoji_url = item_emoji["url"]
                    emoji_id = item_emoji["id"]
                    emoji_name = item_emoji["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}> "
                
                else:
                    print(item[1]["id"])
                    item_emoji = ""

            else:
                print(item[1]["id"])
                item_emoji = ""

        items_string += f"↳ {item_emoji}{count(item[1], super_suffix)}{suffix} (**{numerize(item[1]['price'])}**)\n"

    if items_string == "":
        return None

    return {
        "name": f"{emoji} {name} ({numerize(total_value)})",
        "value": items_string,
        "inline": False
    }