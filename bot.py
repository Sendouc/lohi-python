import discord
from discord.ext import commands
import traceback

from cogs.utils import config, ids, api
from cogs.utils.on_message import on_competitive_feed_post

INITIAL_EXTENSIONS = (
    "cogs.splatoon",
    "cogs.misc",
    "cogs.admin",
    "cogs.tourney",
    "cogs.sniping",
)

bot = commands.Bot(command_prefix=".", case_insensitive=True)

if __name__ == "__main__":
    for extension in INITIAL_EXTENSIONS:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    bot.api = api.ApiConnecter()
    # http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready
    print(
        f"\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n"
    )
    print(f"Successfully logged in and booted!")


# @bot.event
# async def on_message(message: discord.Message):
# if message.channel.id == ids.COMPETITIVE_FEED_CHANNEL:
#    await on_competitive_feed_post(message, bot)


@bot.check
async def check_if_channel_white_listed(ctx):
    """
    Commands can only be used on white listed channels or DM's. 
    The owner user can use them anywhere.
    """
    if ctx.author.id == ids.OWNER_ID:
        return True

    if ctx.guild is None:
        return True

    if ctx.channel.id in ids.WHITELISTED_CHANNELS:
        return True

    for r in ctx.author.roles:
        if r.name == "Staff":
            return True

    return False


@bot.event
async def on_error(event, *args, **kwargs):
    """
    If a command causes error a DM is sent to the owner with the stack trace 
    and the user of the command is notified.
    """
    # Gets the ctx object
    context = args[0]
    master_user = bot.get_user(ids.OWNER_ID)
    if master_user is None:
        master_user = await bot.fetch_user(ids.OWNER_ID)
    error_msg = f"```{traceback.format_exc()}```"
    if event == "on_command_error":
        await master_user.send(
            f"Error caused by this message from {context.message.author}:\n"
            f"```{context.message.content}```"
        )
    else:
        await master_user.send(f"Error happened with the code {event}")
    await master_user.send(error_msg[:2000])
    await context.send("Your command caused an error.")


@bot.event
async def on_command_error(ctx, error):
    ignored_errors = [commands.CommandNotFound, commands.CheckFailure]
    for err in ignored_errors:
        if isinstance(error, err):
            return
    raise error


bot.run(config.TOKEN, bot=True, reconnect=True)
