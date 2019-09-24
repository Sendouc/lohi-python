import discord
from discord.ext import commands

from .utils import ids

class TournamentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        if len(team_name) > 30:
            return await ctx.send(f"Team name is too long. It has be to be 30 or less but it was {len(team_name)} characters long.")
        
        role = None
        for r in ctx.message.guild.roles:
            if r.name == TOURNAMENT_PARTICIPANT_ROLE_NAME:
                role = r
        await member.add_roles(role)

        if new_name is None:
            new_name = member.name

        new_nick = f"[{team_name}] {new_name}"[:32]

        await member.edit(nick=new_nick)
        await ctx.send(f"Done! New nickname: {new_nick}")

def setup(bot):
    bot.add_cog(TournamentCog(bot))