import discord
from discord.ext import commands

from .utils.lists import map_part_to_full, mode_part_to_full, modes_to_emoji

class SplatoonCog(commands.Cog, name="Splatoon"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='rot')
    async def display_rotation(self, ctx, *maps_or_modes):
        '''
        Displays the rotation with optional parameters to 
        filter the result. Example usage:
        '''
        ok_maps = set()
        ok_modes = set()
        for m in maps_or_modes:
            if m.lower() in map_part_to_full:
                ok_maps.add(map_part_to_full[m])
            elif m.lower() in mode_part_to_full:
                ok_modes.add(mode_part_to_full[m])
            else:
                return await ctx.send(f"""Unfortunately I'm not sure 
                what map or mode {m} is referring to, {ctx.message.author.name}""")

        if "Turf War" in ok_modes:
            pass
        else:

        


def setup(bot):
    bot.add_cog(SplatoonCog(bot))