# https://discordapp.com/developers/docs/resources/channel#embed-limits

import discord

from ..lists import (
    weapons_english_internal,
    abilities_short_to_emoji,
    top_500_emoji,
    weapons_to_emoji,
)

# Cheers to Lean
class LohiEmbed:
    def __init__(
        self,
        title="\uFEFF",
        description="\uFEFF",
        color=0x60DD8E,
        url=None,
        footer="\uFEFF",
    ):
        self.title = title
        self.description = description
        self.color = color
        self.url = url
        self.fields = []
        self.footer = footer

    def add_field(self, name="\uFEFF", value="\uFEFF", inline=True):
        self.fields.append((name, value, inline))

    def add_weapon_build_fields(self, builds):
        for build in builds:
            title = build["title"]
            discord_tag = f"{build['discord_user']['username']}#{build['discord_user']['discriminator']}"
            if title:
                title = f"{title} by {discord_tag}"
            else:
                title = f"{discord_tag}"
            ability_arrs = [build["headgear"], build["clothing"], build["shoes"]]
            ability_str = ""
            for arr in ability_arrs:
                for count, ability in enumerate(arr):
                    ability_str += abilities_short_to_emoji[ability]
                    if count == 0:
                        ability_str += "|"
                ability_str += "\n"
            self.add_field(title, ability_str, False)

        if len(self.fields) == 0:
            self.add_field(value="No builds found!")

    def get_embeds(self):
        title = self.title[: 256 - 8]
        desc = self.description[:2048]

        used_up = len(title) + len(desc)
        embed = discord.Embed(
            title=title, description=desc, color=self.color, url=self.url
        )
        embed.set_footer(text=self.footer)

        returned_embeds = []
        for i in range(len(self.fields)):
            name, value, inline = self.fields[i]
            name = name[:256]
            value = value[:1024]
            additional = len(name) + len(value)
            if i % 25 == 24 or used_up + additional > 6000:
                returned_embeds.append(embed)
                title = self.title + " (cont.)"
                embed = discord.Embed(
                    title=title, description=desc, color=self.color, url=self.url
                )
                embed.set_footer(text=self.footer)
                used_up = len(title) + len(desc)

            used_up += additional
            embed.add_field(name=name, value=value, inline=inline)

        returned_embeds.append(embed)
        return returned_embeds
