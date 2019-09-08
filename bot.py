import discord
from discord.ext import commands
import traceback

from cogs.utils import config

INITIAL_EXTENSIONS = ['cogs.misc', 'cogs.admin']

bot = commands.Bot(command_prefix='.', case_insensitive=True, guild_subscriptions=False, max_messages=None)

if __name__ == '__main__':
    for extension in INITIAL_EXTENSIONS:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    "http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Successfully logged in and booted!')

@bot.check
async def check_if_channel_white_listed(ctx):
    "Commands can only be used on white listed channels or DM's. The owner user can use them anywhere."
    return ctx.message.author.id == config.OWNER_ID or ctx.guild is None or ctx.message.channel.id in config.WHITELISTED_CHANNELS

@bot.event
async def on_error(event, *args, **kwargs):
	"If a command causes error a DM is sent to the owner with the stack trace and the user of the command is notified."
	# Gets the ctx object
	context = args[0]
	master_user = bot.get_user(config.OWNER_ID)
	if master_user is None:
		master_user = await bot.fetch_user(config.OWNER_ID)
	error_msg = f"```{traceback.format_exc()}```"
	await master_user.send(f"Error caused by this message from {context.message.author}:\n"
							f"```{context.message.content}```")
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