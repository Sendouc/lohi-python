import discord
from discord.ext import commands
import os
import gspread
import pymongo
import asyncio
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

from .utils import ids
from .utils.classes.VotedPlayer import VotedPlayer
from .utils.helper import split_to_shorter_parts
from .utils.lists import weapons


class AdminCog(commands.Cog, name="Admin"):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command(name="voting")
    async def display_voting_results(self, ctx, plus_two: str = ""):
        """
        Fetches voting results from Google Sheets
        and parses them into an info post to a 
        designated channel.
        """
        plus_two = True if plus_two == "+2" else False
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        script_dir = os.path.dirname(__file__)
        rel_path = "google_sheet_secret.json"
        abs_file_path = os.path.join(script_dir, rel_path)
        sheets = gspread.authorize(
            ServiceAccountCredentials.from_json_keyfile_name(abs_file_path, scope)
        )
        sheet_url = "+2 server" if plus_two else "+1 server"
        sheet = sheets.open(sheet_url)
        worksheet = sheet.get_worksheet(0)

        # Get all votes as list of lists
        votes = worksheet.get_all_values()
        players_voted_on = []

        server_id = ids.PLUSTWO_SERVER_ID if plus_two else ids.PLUSONE_SERVER_ID
        plusone = self.bot.get_guild(server_id)
        for title in votes[0]:
            if "Vote" in title:
                # Finding if the member is NA or not
                discord_id = int(title.split("<@")[1].split(">")[0])
                member = plusone.get_member(discord_id)
                is_na = None
                if member:
                    for r in member.roles:
                        if r.name == "EU":
                            is_na = False
                            break
                        elif r.name == "NA":
                            is_na = True
                            break
                # It is asked if the voted is EU or NA only if we're not in +2 server OR the person in question wasn't a suggested one
                if is_na is None and (not plus_two or not "*" in title):
                    await ctx.send(
                        f"Is {title.replace('Vote [', '').replace(']', '').replace('[*', '')} `NA` or `EU`?"
                    )

                    def confirm_check(m):
                        return (
                            m.content.upper() == "NA" or m.content.upper() == "EU"
                        ) and m.author == ctx.message.author

                    try:
                        msg = await self.bot.wait_for(
                            "message", timeout=120.0, check=confirm_check
                        )
                        if msg.content.upper() == "NA":
                            is_na = True
                        else:
                            is_na = False
                    except asyncio.TimeoutError:
                        return await ctx.send(f"Assigning region timed out.")

                if "[*]" in title:
                    title_parts = title.split("[")
                    name = title_parts[1].strip()
                    if name == "":
                        return await ctx.send("Empty name detected.")
                    player = VotedPlayer(
                        name=name, id=discord_id, suggested=True, na=is_na
                    )
                    players_voted_on.append(player)
                else:
                    title_parts = title.split("[")
                    name = title_parts[1][:-1].strip()
                    if name == "":
                        return await ctx.send("Empty name detected.")
                    player = VotedPlayer(name=name, id=discord_id, na=is_na)
                    players_voted_on.append(player)

        del votes[0]
        names = []

        # Check if someone voted twice.
        for row in votes:
            name_lower = row[1].lower()
            if name_lower in names:
                return await ctx.send(f"Duplicate name found: {row[1]}")
            names.append(name_lower)

        na_ballots = 0
        eu_ballots = 0
        for row in votes:
            voter_id = int(row[1].split("<@")[1].split(">")[0])
            member = plusone.get_member(voter_id)
            is_na = None
            for p in players_voted_on:
                if p.id == voter_id:
                    is_na = p.na

            if is_na:
                na_ballots += 1
            else:
                eu_ballots += 1

            # First two rows contain timestamp and voter id
            # needed so the count finds the right player
            for count, vote in enumerate(row[2:]):
                # Last rows contain question(s)
                if vote not in ["+2", "+1", "-1", "-2"]:
                    continue
                player = players_voted_on[count]
                if vote == "+2":
                    player.add_vote(2, is_na)
                elif vote == "+1":
                    player.add_vote(1, is_na)
                elif vote == "-1":
                    player.add_vote(-1, is_na)
                else:
                    player.add_vote(-2, is_na)

        players_voted_on.sort(reverse=True)
        votes_in_total = len(votes)
        now = datetime.now()
        month_year_str = now.strftime("%B %Y")
        to_be_said = [f"__**{month_year_str.upper()}**__\n"]
        to_be_said_existing_players = [
            "*Vote ratio is between -2 and 2. "
            "It is your votes summed up divided by the amount of ballots. "
            "Followed is the exact amount of different kind of votes you got in order "
            f"(-2/-1/+1/+2)*\n\n-- **Players in +{'2' if plus_two else '1'}** --\n\n"
        ]
        suggest_string = (
            "\n-- **Players suggested to +2** --\n\n"
            if plus_two
            else "\n-- **Players suggested to +1** --\n\n"
        )
        to_be_said_suggested_players = [suggest_string]

        total_ratios = 0.0
        for player in players_voted_on:
            vote_ratio = player.get_vote_ratio()
            total_ratios += float(vote_ratio)

            if player.suggested:
                to_be_said_suggested_players.append(f"{str(player)}\n")
            else:
                to_be_said_existing_players.append(f"{str(player)}\n")

        to_be_said.extend(to_be_said_existing_players)
        to_be_said.extend(to_be_said_suggested_players)

        average_score_ratio = total_ratios / (na_ballots + eu_ballots)
        to_be_said.append(
            f"\n*{eu_ballots+na_ballots} votes (NA: {na_ballots} EU: {eu_ballots})\n"
            f"Average: {'%+.2f' % round(average_score_ratio, 2)}*"
        )

        results_channel_id = (
            ids.PLUSTWO_VOTING_RESULT_CHANNEL_ID
            if plus_two
            else ids.PLUSONE_VOTING_RESULT_CHANNEL_ID
        )
        voting_result_channel = self.bot.get_channel(results_channel_id)
        if voting_result_channel is None:
            voting_result_channel = await self.bot.fetch_channel(results_channel_id)

        await voting_result_channel.set_permissions(
            plusone.default_role,
            read_messages=False,
            add_reactions=False,
            send_messages=False,
        )
        for msg in split_to_shorter_parts("".join(to_be_said)):
            await voting_result_channel.send(msg)

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
