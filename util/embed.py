import discord
from numerize.numerize import numerize
from .formatting import count

def get_embed(text, bot):
    embed = discord.Embed(
        description=text,
        color=discord.Color.blue()
    ).set_author(name=bot.user.name, icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    return embed

# dont judge the ugly shit

def generate_embed_networth_field(items, total_value, name, emoji, emojis, item_emojis):
    items = sorted(items, key=lambda x: x["price"], reverse=True)
    items_string = ""
    for item in enumerate(items):
        item_id = item[1]["id"]
        item_type = item[1].get("type")
        item_skin = item[1].get("skin")
        item_held_item = item[1].get("heldItem")

        if item[0] == 5:
            items_string += f"... **{len(items) - 5} more**"
            break

        super_suffix = None
        suffix = ""
        for calc in item[1]["calculation"]:
            if calc["id"] == "RECOMBOBULATOR_3000":
                suffix += " "+emojis.recombobulator_3000

        if item_id.startswith("starred_"):
            item_id = item_id[8:]

        item_emoji = item_emojis.get(item_id.upper())
        if item_type:
            if item_skin is None:
                item_emoji = item_emojis.get("PET_"+item_type.upper())

            else:
                item_emoji = item_emojis.get("PET_SKIN_"+item_skin.upper())

            if item_held_item:
                supersuffix_emoji = item_emojis.get(item_held_item.upper())
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
            if "new_year_cake" in item_id.lower() and "bag" not in item_id.lower():
                item_emoji_data = item_emojis.get("NEW_YEAR_CAKE")
                emoji_id = item_emoji_data["id"]
                emoji_name = item_emoji_data["name"]
                item_emoji = f"<:{emoji_name}:{emoji_id}> "

            elif "_skinned_" in item_id:
                item_emoji_name = item_id.split("_skinned_")[1]
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
                    print(item_id)
                    item_emoji = ""

            elif item_id.endswith("_shiny"):
                item_emoji_name = item_id[:-6]
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
                    print(item_id)
                    item_emoji = ""

            elif item_id.endswith("_uneditioned"):
                item_emoji_name = item_id.replace("_uneditioned", "")
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
                    print(item_id)
                    item_emoji = ""

            else:
                print(item_id)
                item_emoji = ""

        items_string += f"↳ {item_emoji}{count(item[1], super_suffix)}{suffix} (**{numerize(item[1]['price'])}**)\n"

    if items_string == "":
        return None

    return {
        "name": f"{emoji} {name} ({numerize(total_value)})",
        "value": items_string,
        "inline": False
    }