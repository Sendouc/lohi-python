import discord
from discord.ext import commands
from cogs.utils import config, ids
import datetime


async def on_competitive_feed_post(message: discord, bot: commands.Bot):
    comp_feed_info = bot.get_channel(ids.COMPETITIVE_FEED_INFO)
    parts = message.clean_content.strip().split("\n")
    if len(parts) < 3:
        await message.delete()
        return await comp_feed_info.send(
            f" {message.author.mention} your message was deleted because it doesn't follow the format. Please see the pins for an example."
        )
    tournament_name = parts[0]
    iso_string = parts[1]

    description = "\n".join(parts[2:]).strip()
    discord_invite_url = None

    for word in description.split(" "):
        if "https://discord.gg/" in word:
            discord_invite_url = word
            break

    if discord_invite_url is None:
        await message.delete()
        return await comp_feed_info.send(
            f" {message.author.mention} your message was deleted because it didn't contain a valid Discord server link with the format `https://discord.gg/xxxxx`. Please see the pins for an example."
        )

    try:
        date = datetime.datetime.fromisoformat(iso_string)
    except ValueError:
        await message.delete()
        return await comp_feed_info.send(
            f" {message.author.mention} your message was deleted because the date `{iso_string}` is invalid. Please see the pins for an example."
        )

    picture_url = None
    if len(message.attachments) > 0:
        picture_url = message.attachments[0].url

    params = {
        "event": {
            "name": tournament_name,
            "date": str(int(date.timestamp() * 1000)),
            "description": description,
            "poster_discord_id": str(message.author.id),
            "poster_username": message.author.name,
            "poster_discriminator": message.author.discriminator,
            "message_discord_id": str(message.id),
            "discord_invite_url": discord_invite_url,
            "message_url": message.jump_url,
            "picture_url": picture_url,
        },
        "lohiToken": config.LOHI_TOKEN,
    }

    result = await bot.api.add_competitive_feed_event(**params)

    if result:
        await message.add_reaction("✅")
