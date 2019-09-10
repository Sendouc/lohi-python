import discord
from discord.ext import commands

class SplatoonCog(commands.Cog, name="Splatoon"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='rot')
    async def display_rotation(self, ctx, *args):
        '''
        Displays the rotation with optional parameters to 
        filter the result. Example usage:
        '''
        print(await self.bot.api.get_rotation_data())

def setup(bot):
    bot.add_cog(SplatoonCog(bot))