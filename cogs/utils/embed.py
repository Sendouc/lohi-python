# https://discordapp.com/developers/docs/resources/channel#embed-limits

import discord

from .lists import weapons_english_internal, abilities_short_to_emoji, top_500_emoji, weapons_to_emoji

GLOBAL_COLOR = 0x60dd8e

def add_fields(embed: discord.Embed, field_adder: function):
    

def weapon_builds(builds: dict, weapon: str) -> List[discord.Embed]:
    wpn_emoji = weapons_to_emoji[weapon]
    embed = discord.Embed(title=f"{wpn_emoji} {weapon} Builds", url=f"https://sendou.ink/builds/{weapon.replace(' ', '_')}", color=GLOBAL_COLOR)

    def add_field():
        for build in builds:
            title = build['title']
            discord_tag = f"{build['discord_user']['username']}#{build['discord_user']['discriminator']}"
            if title:
                title = f"{title} by {discord_tag}"
            else:
                title = f"{discord_tag}"
            top500 = build["top"]
            if top500:
                title = f"{top_500_emoji} {title}"
            ability_arrs = [build["headgear"], build["clothing"], build["shoes"]]
            ability_str = ""
            for arr in ability_arrs:
                for count, ability in enumerate(arr):
                    ability_str += abilities_short_to_emoji[ability]
                    if count == 0:
                        ability_str += "|"
                ability_str += "\n"

            embed.add_field(name=title, value=ability_str, inline=False)
    print(len(embed))
    return embed