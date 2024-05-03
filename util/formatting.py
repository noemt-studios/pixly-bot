def count(item, emoji=None):
    item_name = item.get("name")
    if item.get("count", 1) == 1:
        if "✦" in item_name and emoji is not None:
            return item_name.replace("✦", emoji)
        return item_name
        
    else:
        if "✦" in item_name and emoji is not None:
            return f"`{item['count']}x` {item_name.replace('✦', emoji)}"
        
        return f"`{item['count']}x` {item_name}"