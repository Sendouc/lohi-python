import discord
import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from discord.ext import commands

from .utils import ids
from .utils.classes.VotedPlayer import VotedPlayer
from .utils.helper import split_to_shorter_parts

class AdminCog(commands.Cog, name="Admin"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        ''' 
        Check that makes sure nobody else but me uses the commands here.
        '''
        return ctx.message.author.id == ids.OWNER_ID

    @commands.command(name='removeall')
    async def remove_role_from_members(self, ctx, role: discord.Role):
        '''
        Takes the given role and removes it from all
        members that have it.
        '''
        for member in role.members:
            await member.remove_roles(role)
        await ctx.send (f'All done with removing {role.name} from the users.')

    @commands.command(name='emo')
    async def emoji_to_string(self, ctx, emoji: discord.Emoji):
        '''
        Displays a bot friendly string of the emoji given.
        '''
        await ctx.send(f"`<:{emoji.name}:{emoji.id}>`")

    @commands.command(name='voting')
    async def display_voting_results(self, ctx):
        '''
        Fetches voting results from Google Sheets
        and parses them into an info post to a 
        designated channel.
        '''
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        script_dir = os.path.dirname(__file__)
        rel_path = "google_sheet_secret.json"
        abs_file_path = os.path.join(script_dir, rel_path)
        sheets = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name(abs_file_path, scope))
        sheet = sheets.open("+1 server")
        worksheet = sheet.get_worksheet(0)

        # Get all votes as list of lists
        votes = worksheet.get_all_values()
        players_voted_on = []

        for title in votes[0]:
            if "Vote" in title:
                if "[*]" in title:
                    title_parts = title.split("[")
                    name = title_parts[1].strip()
                    player = VotedPlayer(name, suggested=True)
                    players_voted_on.append(player)
                else:
                    title_parts = title.split("[")
                    name = title_parts[1][:-1]
                    player = VotedPlayer(name)
                    players_voted_on.append(player)

        del votes[0]
        names = []

        # Check if someone voted twice.
        for row in votes:
            name_lower = row[1].lower()
            if name_lower in names:
                await ctx.send(f"Duplicate name found: {row[1]}")

        na_ballots = 0
        eu_ballots = 0
        plusone = self.bot.get_guild(ids.PLUSONE_SERVER_ID)
        for row in votes:
            voter_id = int(row[1].split("<@")[1].split(">")[0])
            member = plusone.get_member(voter_id)
            if member is None:
                member = await plusone.fetch_member(voter_id)
            is_na = None
            for r in member.roles:
                if r.name == "EU":
                    is_na = False
                    eu_ballots += 1
                    break
                elif r.name == "NA":
                    is_na = True
                    na_ballots += 1
                    break
            if is_na is None:
                raise ValueError(f"{member.name} doesn't have region role")

            # First two columns contain time stamp and name of the voter so we ignore them.
            for count, vote in enumerate(row[2:-1]):
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
        to_be_said_existing_players = ["*Vote ratio is between -2 and 2. "
        "It is your votes summed up divided by the amount of ballots. "
        "Followed is the exact amount of different kind of votes you got in order "
        "(-2/-1/+1/+2)*\n\n-- **Players in +1** --\n\n"]
        to_be_said_suggested_players = ["\n-- **Players suggested to +1** --\n\n"]

        total_ratios = 0.0
        for player in players_voted_on:
            vote_ratio = player.get_vote_ratio()
            total_ratios += float(vote_ratio)
            eu_vote_ratio = player.get_regional_vote_ratio(False)
            na_vote_ratio = eu_vote_ratio = player.get_regional_vote_ratio(True)

            if player.suggested:
                to_be_said_suggested_players.append(f"{str(player)}\n")
            else:
                to_be_said_existing_players.append(f"{str(player)}\n")

        to_be_said.extend(to_be_said_existing_players)
        to_be_said.extend(to_be_said_suggested_players)

        average_score_ratio = total_ratios/(na_ballots+eu_ballots)
        to_be_said.append(f"\n*{eu_ballots+na_ballots} votes (NA: {na_ballots} EU: {eu_ballots})\n"
        f"Average: {'%+.2f' % round(average_score_ratio, 2)}*")

        voting_result_channel = self.bot.get_channel(ids.PLUSONE_VOTING_RESULT_CHANNEL_ID)
        if voting_result_channel is None:
            voting_result_channel = await self.bot.fetch_channel(ids.PLUSONE_VOTING_RESULT_CHANNEL_ID)
        
        await voting_result_channel.set_permissions(plusone.default_role, read_messages=False)
        for msg in split_to_shorter_parts("".join(to_be_said)):
            await voting_result_channel.send(msg)
        
    # https://gist.github.com/EvieePy/d78c061a4798ae81be9825468fe146be

    @commands.command(name='r')
    async def reload_cog(self, ctx, *, cog):
        '''
        Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner
        '''
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('Reloading the cog was succesful.')

    @commands.command(name='update')
    async def update(self, ctx):
        '''
        Use git pull to update the bot. Courtesy of Lean.
        '''
        import subprocess 
        with subprocess.Popen(["git",  "pull"], stdout=subprocess.PIPE, encoding="utf-8") as proc:
            stdout_read = proc.stdout.read()
            await ctx.send(f"```sh\n{stdout_read}```")
        if "Already up to date." not in stdout_read:
            await self.bot.close()

def setup(bot):
    bot.add_cog(AdminCog(bot))
