def build_discord_embed(title, colour, fields, thumbnail=None, footer=None, url=None, description=None):
    embed = {
        "title": title,
        "color": colour,
        "fields": fields,
    }
    if thumbnail:
        embed["thumbnail"] = thumbnail
    if footer:
        embed["footer"] = footer
    if url:
        embed["url"] = url
    if description:
        embed["description"] = description
    return embed
