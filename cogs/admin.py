import discord
from discord.ext import commands, tasks
import os
import gspread
import pymongo
import asyncio
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

from .utils import ids, config
from .utils.classes.VotedPlayer import VotedPlayer
from .utils.helper import split_to_shorter_parts
from .utils.lists import weapons


class AdminCog(commands.Cog, name="Admin"):
    def __init__(self, bot):
        self.bot = bot
        self.skip_loop = True

    async def cog_check(self, ctx):
        """ 
        Check that makes sure nobody else but me uses the commands here.
        """
        return ctx.message.author.id == ids.OWNER_ID

    @commands.command(name="test")
    async def test_command(self, ctx):
        await ctx.send("test!")

    @commands.command(name="removeall")
    async def remove_role_from_members(self, ctx, role: discord.Role):
        """
        Takes the given role and removes it from all
        members that have it.
        """
        for member in role.members:
            await member.remove_roles(role)
        await ctx.send(f"All done with removing {role.name} from the users.")

    @commands.command(name="deleteunusedcolor")
    async def delete_ununused_color_roles(self, ctx):
        """
        Deletes any role that has '!' in the name
        and nobody has currently
        """
        if not ctx.message.guild:
            return await ctx.send("You are not in a server.")

        to_be_said = ""
        for role in ctx.message.guild.roles:
            if "!" in role.name and len(role.members) == 0:
                await role.delete()
                to_be_said += f"{role.name}\n"

        if len(to_be_said) == 0:
            return await ctx.send("No roles to delete.")
        await ctx.send(f"Deleted:\n{to_be_said}")

    @commands.command(name="emo")
    async def emoji_to_string(self, ctx, emoji: discord.Emoji):
        """
        Displays a bot friendly string of the emoji given.
        """
        await ctx.send(f"`<:{emoji.name}:{emoji.id}>`")

    # https://gist.github.com/EvieePy/d78c061a4798ae81be9825468fe146be

    @commands.command(name="r")
    async def reload_cog(self, ctx, *, cog):
        """
        Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner
        """
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("Reloading the cog was succesful.")

    @commands.command(name="update")
    async def update(self, ctx):
        """
        Use git pull to update the bot. Courtesy of Lean.
        """
        import subprocess

        with subprocess.Popen(
            ["git", "pull"], stdout=subprocess.PIPE, encoding="utf-8"
        ) as proc:
            stdout_read = proc.stdout.read()
            await ctx.send(f"```sh\n{stdout_read}```")
        if "Already up to date." not in stdout_read:
            await self.bot.close()


def setup(bot):
    bot.add_cog(AdminCog(bot))
