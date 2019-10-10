import discord
from discord.ext import commands
import asyncio
import challonge

from .utils import ids
from .utils import config

class TournamentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.challonge_user = None

    async def cog_check(self, ctx):
        ''' 
        These commands can be used only by members with
        the "Staff" role.
        '''
        STAFF_ROLE_NAME = "Staff"

        if ctx.message.guild is None:
            return False

        if ctx.message.guild.id != ids.SENDOU_SERVER_ID:
            return False

        for r in ctx.message.author.roles:
            if r.name == STAFF_ROLE_NAME:
                return True
        
        return False

    async def cog_before_invoke(self, ctx):
        if self.challonge_user is None:
            self.challonge_user = await challonge.get_user(config.CHALLONGE_USER_NAME, config.CHALLONGE_API_KEY)

    @commands.command(name='part')
    async def change_name_and_give_participant_role(self, ctx, member: discord.Member, team_name: str, new_name: str = None):
        '''
        Changes the participant name to fit the format
        and gives them the participant role.
        Example usage: .part Sendou#0043 "Team Olive"
        (notice the " " around the team name)
        '''
        TOURNAMENT_PARTICIPANT_ROLE_NAME = "Tournament Participant"

        if not member:
            return await ctx.send("Member with that name couldn't be found.")

        for r in ctx.message.guild.roles:
            if r.name == TOURNAMENT_PARTICIPANT_ROLE_NAME:
                role = r

        # Checking if another member of this team already claimed a role
        for team_captain in role.members:
            existing_team_name = team_captain.nick.split("[")[1].split("]")[0]
            if team_name.upper() == existing_team_name.upper():
                return await ctx.send(f"There already is a captain for {team_name}")

        if len(team_name) > 30:
            return await ctx.send(f"Team name is too long. It has be to be 30 or less but it was {len(team_name)} characters long.")

        await member.add_roles(role)

        if new_name is None:
            new_name = member.name

        new_nick = f"[{team_name}] {new_name}"[:32]

        await member.edit(nick=new_nick)
        await ctx.send(f"Done! New nickname: {new_nick}")

    @commands.command(name='track')
    async def post_participant_change_of_tournament(self, ctx):
        '''
        Tracks the tournament given and posts participants joining
        or leaving to channel.
        '''
        tourneys = await self.challonge_user.get_tournaments("sendous")
        for participant in await tourneys[0].get_participants():
            print(participant.challonge_username)

def setup(bot):
    bot.add_cog(TournamentCog(bot))