import constants
import asyncio

def has_accessory(accessories, accessory, options=None):
    if options is None:
        options = {'ignoreRarity': False}


    id = accessory['id'] if isinstance(accessory, dict) else accessory

    if not options['ignoreRarity']:
        return any(a.get('id') == id and constants.RARITIES.index(a['rarity']) >= constants.RARITIES.index(accessory['rarity']) for a in accessories)
    else:
        return any(a.get('id') == id for a in accessories)

def get_accessory(accessories, accessory):
    return next((a for a in accessories if a['id'] == accessory), None)

def get_missing(accessories):
    ACCESSORIES = constants.getAllAccessories()
    unique = [{'id': a['id'], 'rarity': a.get('tier', "admin")} for a in ACCESSORIES]

    for u in unique:
        id = u['id']
        if id not in constants.ACCESSORY_ALIASES:
            continue

        for duplicate in constants.ACCESSORY_ALIASES[id]:
            if has_accessory(accessories, duplicate, {'ignoreRarity': True}):
                get_accessory(accessories, duplicate)['id'] = id

    missing = [a for a in unique if not has_accessory(accessories, a)]
    for m in missing:
        id = m['id']
        upgrades = constants.get_upgrade_list(id)
        if upgrades is None:
            continue

        for upgrade in [u for u in upgrades if upgrades.index(u) > upgrades.index(id)]:
            if has_accessory(accessories, upgrade):
                missing = [m for m in missing if m['id'] != id]

    upgrades = []
    other = []
    for m in missing:
        id = m['id']
        rarity = m['rarity']
        ACCESSORY = next((a for a in ACCESSORIES if a['id'] == id and a.get('tier') == rarity), None)

        if ACCESSORY:
            object = {
                **ACCESSORY,
                'display_name': ACCESSORY.get('name', None),
                'rarity': rarity,
            }

            if object.get('category', "") != "accessory":
                continue 

            if (constants.get_upgrade_list(id) and constants.get_upgrade_list(id)[0] != id):
                upgrades.append(object)
            else:
                other.append(object)

    return {
        'missing': other,
        'upgrades': upgrades,
    }
