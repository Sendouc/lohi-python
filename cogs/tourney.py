import discord
from discord.ext import commands
import asyncio
from math import log, ceil

from .utils import ids
from .utils import config
from .utils.map_generator import map_generation
from .utils.lists import maps
from .utils.helper import split_to_shorter_parts


class TournamentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """ 
        These commands can be used only by members with
        the "Staff" role.
        """
        STAFF_ROLE_NAME = "Staff"

        if ctx.message.guild is None:
            return False

        if ctx.message.guild.id != ids.SENDOU_SERVER_ID:
            return False

        for r in ctx.message.author.roles:
            if r.name == STAFF_ROLE_NAME:
                return True

        return False

    @commands.command(name="part")
    async def change_name_and_give_participant_role(
        self, ctx, member: discord.Member, team_name: str, new_name: str = None
    ):
        """
        Changes the participant name to fit the format
        and gives them the participant role.
        Example usage: .part Sendou#0043 "Team Olive"
        (notice the " " around the team name)
        """
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
            return await ctx.send(
                f"Team name is too long. It has be to be 30 or less but it was {len(team_name)} characters long."
            )

        await member.add_roles(role)

        if new_name is None:
            new_name = member.name

        new_nick = f"[{team_name}] {new_name}"[:32]

        await member.edit(nick=new_nick)
        await ctx.send(f"Done! New nickname: {new_nick}")

    @commands.command(name="tourneymaps")
    async def generate_and_post_maps_for_tournament(
        self, ctx, amount_of_teams: int, ruleset: str = "ITZ"
    ):
        """
        Bot generates a list of maps to use for tournament
        and says it.
        """
        events = {"ITZ": {"map_pool": {"sz": maps.copy()}}}
        if ruleset.upper() not in events:
            return await ctx.send(f"{ruleset} is not a valid ruleset.")

        L2 = log(amount_of_teams, 2)
        # Winners includes grand finals
        winner_map_amount = ceil(L2) + 1
        loser_map_amount = ceil(L2) + ceil(log(L2, 2)) - 1

        games = []
        games_enum = []
        if ruleset == "ITZ":
            games.extend([3, 3, 3])
            games_enum.extend(["WINNER", "LOSER", "WINNER"])
            winner_map_amount -= 2
            loser_map_amount -= 1
            while winner_map_amount > 0 or loser_map_amount > 0:
                if winner_map_amount == 1:
                    games.extend([7, 7])
                    games_enum.extend(["WINNER", "WINNER"])
                    winner_map_amount -= 1
                elif winner_map_amount > 0:
                    games.append(5)
                    games_enum.append("WINNER")
                    winner_map_amount -= 1

                if loser_map_amount == 1:
                    games.append(5)
                    games_enum.append("LOSER")
                    loser_map_amount -= 1
                elif loser_map_amount > 0:
                    games.append(3)
                    games_enum.append("LOSER")
                    loser_map_amount -= 1

        generated_maps = map_generation(
            map_pool=events[ruleset]["map_pool"], games=games
        )

        winner_map_str = "__**WINNERS**__\n\n"
        losers_map_str = "__**LOSERS**__\n\n"

        winner_map_count = ceil(L2) + 2
        losers_round = 1
        winners_round = 1
        print_modes = ruleset.upper() not in ["ITZ", "DRAFT"]
        for map_tuple in list(zip(games_enum, generated_maps)):
            enum, maplist = map_tuple

            if enum == "LOSER":
                losers_map_str += f"Losers Round {losers_round}\n```"
                for count, stage_tuple in enumerate(maplist, 1):
                    mode, stage = stage_tuple
                    mode = f"{mode} on " if print_modes else ""
                    losers_map_str += f"{count}) {mode}{stage}\n"
                losers_map_str += "```\n"
                losers_round += 1
            else:
                title = f"Round {winners_round}"
                if winner_map_count == 3:
                    title = "Semifinals"
                elif winner_map_count == 2:
                    title = "Finals"
                elif winner_map_count == 1:
                    title = "Finals (Bracket Reset)"
                winner_map_str += f"{title}\n```"
                for count, stage_tuple in enumerate(maplist, 1):
                    mode, stage = stage_tuple
                    mode = f"{mode} on " if print_modes else ""
                    winner_map_str += f"{count}) {mode}{stage}\n"
                winner_map_str += "```\n"
                winners_round += 1
                winner_map_count -= 1

        before_all = (
            "Mode: Splat Zones\n\n" if ruleset.upper() in ["ITZ", "DRAFT"] else ""
        )
        for line in split_to_shorter_parts(
            before_all + winner_map_str + losers_map_str
        ):
            await ctx.send(line)


def setup(bot):
    bot.add_cog(TournamentCog(bot))
