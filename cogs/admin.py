import discord
from discord.ext import commands
import requests

from .utils import config

class AdminCog(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """ Check that makes sure nobody else but me uses the commands here. """
        return ctx.message.author.id == config.OWNER_ID

    @commands.command(name='removeall')
    async def remove_role_from_members(self, ctx, role: discord.Role):
        """Takes the given role and removes it from all
            members that have it."""
        for member in role.members:
            await member.remove_roles(role)
        await ctx.send (f'All done with removing {role.name} from the users.')

    # https://gist.github.com/EvieePy/d78c061a4798ae81be9825468fe146be

    @commands.command(name='r')
    async def reload_cog(self, ctx, *, cog):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('Reloading the cog was succesful.')

    @commands.command(name='update')
    async def update(self, ctx):
        """Use git pull to update the bot. Courtesy of Lean."""
        import subprocess 
        with subprocess.Popen(["git",  "pull"], stdout=subprocess.PIPE, encoding="utf-8") as proc:
            stdout_read = proc.stdout.read()
            await ctx.send(f"```sh\n{stdout_read}```")
        if "Already up to date." not in stdout_read:
            await self.bot.close()

def setup(bot):
    bot.add_cog(AdminCog(bot))
