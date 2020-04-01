import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio

from .utils import ids


class SnipingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.snipe_loop.cancel()

    @tasks.loop(minutes=7.0)
    async def snipe_loop(self):
        channel = self.bot.get_channel(ids.LOBBYSNIPING_COUNTDOWN_CHANNEL_ID)
        next_iteration = self.snipe_loop.next_iteration + timedelta(seconds=60)
        guild = self.bot.get_guild(ids.PLUSONE_SERVER_ID)
        category = guild.get_channel(ids.LOBBYSNIPING_CATEGORY_ID)
        if self.snipe_loop.current_loop == 0:
            await category.edit(name=f"Better Lobbies 🎯 NEXT :{next_iteration.minute}")
            return
        await channel.send(
            f"1 minute till it's time to queue up in solo <@&{ids.LOBBYSNIPE_ROLE_ID}>"
        )

        await asyncio.sleep(45)
        await channel.send("15 seconds to go. Get ready!")
        await asyncio.sleep(12)
        await channel.send("3!")
        await asyncio.sleep(1)
        await channel.send("2!")
        await asyncio.sleep(1)
        await channel.send("1!")
        await asyncio.sleep(1)
        await channel.send("Go go go!")
        await category.edit(name=f"Better Lobbies 🎯 NEXT :{next_iteration.minute}")

    @snipe_loop.after_loop
    async def on_cancel(self):
        guild = self.bot.get_guild(ids.PLUSONE_SERVER_ID)
        category = guild.get_channel(ids.LOBBYSNIPING_CATEGORY_ID)
        await category.edit(name=f"Better Lobbies 🎯 OFFLINE")

    @commands.command(name="solo")
    @commands.has_any_role(ids.PLUSONE_ACCESS_ROLE_ID, ids.PLUSTWO_ACCESS_ROLE_ID)
    async def give_or_take_sniping_role(self, ctx):
        """
        Gives or removes the playing solo role.
        """
        role = ctx.guild.get_role(ids.LOBBYSNIPE_ROLE_ID)

        if role in ctx.message.author.roles:
            await ctx.message.author.remove_roles(role)
        else:
            await ctx.message.author.add_roles(role)

        await ctx.message.add_reaction("✅")

    @commands.command(name="snipe")
    @commands.is_owner()
    async def start_or_stop_sniping_loop(self, ctx):
        """
        Start/stop sniping
        """
        if self.snipe_loop.current_loop > 0:
            self.snipe_loop.stop()
        else:
            self.snipe_loop.start()

        await ctx.message.add_reaction("✅")


def setup(bot):
    bot.add_cog(SnipingCog(bot))
