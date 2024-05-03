from constants import HOTM_TREE_MAPPING, SPECIAL_HOTM_TYPES, HOTM_TREE_EMOJIS

def get_hotm_emojis(node_data_raw:dict, selected_ability: str):
    perks_data_raw = []
    for item in node_data_raw:
        item_data = {}
        level = node_data_raw[item]
        item_data["id"] = item
        item_data["level"] = level

        for list in HOTM_TREE_MAPPING:
            for _item in list:
                if _item["type"] == item:
                    max_level = _item["maxLevel"]
                    break

        item_data["maxLevel"] = max_level
        perks_data_raw.append(item_data)


    perks = []
    for item in perks_data_raw:
        perks.append(item["id"])

    perks_data = {}
    for item in perks_data_raw:
        perks_data[item["id"]] = item

    hotm_string = ""
    for row in HOTM_TREE_MAPPING:
        for cell in row:

            if cell["type"] == "empty":
                hotm_string += HOTM_TREE_EMOJIS["empty"]

            elif cell["type"] not in perks and cell["type"] not in SPECIAL_HOTM_TYPES:
                hotm_string += HOTM_TREE_EMOJIS["locked_path"]

            elif cell["type"] not in SPECIAL_HOTM_TYPES:
                perk_data = perks_data[cell["type"]]
                if perk_data["maxLevel"] == perk_data["level"]:
                    hotm_string += HOTM_TREE_EMOJIS["maxed_path"]
                else:
                    hotm_string += HOTM_TREE_EMOJIS["unlocked_path"]

            else:
                if cell["type"] == "special_0":
                    hotm_string += HOTM_TREE_EMOJIS["peak"]

                else:

                    if cell["type"] not in perks_data:
                        hotm_string += HOTM_TREE_EMOJIS["locked_ability"]

                    elif cell["type"] in perks_data and perks_data[cell["type"]]["id"] == selected_ability:
                        hotm_string += HOTM_TREE_EMOJIS["selected_ability"]

                    else:
                        hotm_string += HOTM_TREE_EMOJIS["ability"]
 
        hotm_string += "\n"

    return hotm_string