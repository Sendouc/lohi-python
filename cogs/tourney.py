import discord
from discord.ext import commands
import asyncio
import challonge
import re
from math import log, ceil

from .utils import ids
from .utils import config
from .utils.map_generator import map_generation
from .utils.lists import maps, modes_to_emoji
from .utils.helper import split_to_shorter_parts

TOURNAMENT_URL = "InTheZone15"
TOURNAMENT_PARTICIPANT_ROLE_NAME = "Tournament Participant"


class TournamentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """ 
        These commands can only be used in the Sendou server.
        """
        STAFF_ROLE_NAME = "Staff"

        if not ctx.message.guild or ctx.message.guild.id != ids.SENDOU_SERVER_ID:
            return False

        return True

    @commands.command(name="roles")
    async def give_tournament_roles(
        self, ctx, team_name: str = None, friend_code: str = None
    ):
        """
        After registering on Challonge gives you the roles
        needed for the tournament.
        Example usage: .idk "Team Olive" 0109-3838-9398
        (notice the " " around the team name)
        """
        if team_name is None:
            await ctx.send("No team name provided.")
        if friend_code is None:
            await ctx.send("No friend code provided.")
        user = await challonge.get_user(
            config.CHALLONGE_ACCOUNT_NAME, config.CHALLONGE_TOKEN
        )
        tournament = await user.get_tournament(url=TOURNAMENT_URL, subdomain="sendous")
        participants = await tournament.get_participants()
        team_name_normalized = " ".join(team_name.split()).upper()

        found_name = None
        for participant in participants:
            participant_name = " ".join(participant.display_name.split()).upper()
            if team_name_normalized in participant_name:
                if found_name is not None:
                    return await ctx.send(
                        f"It seems that '{team_name}' can refer to two different teams. Please use unambiguous name."
                    )
                found_name = " ".join(participant.display_name.split())

        if found_name is None:
            return await ctx.send(
                f"No team called {team_name} found. Make sure you are registered to tournament on Challonge."
            )

        found_name = found_name[:30]

        team_name_for_role = f"{found_name} 🏆"

        matched = re.match("[0-9]{4}-[0-9]{4}-[0-9]{4}", friend_code)

        if not bool(matched):
            print(matched)
            return await ctx.send(
                f"Invalid friend code provided. Please follow the pattern: 1234-1234-1234"
            )

        participant_role = None

        for r in ctx.message.guild.roles:
            if r.name == team_name_for_role:
                return await ctx.send("This team already has a captain.")
            elif r.name == friend_code:
                return await ctx.send("This friend code is already in use.")
            if r.name == TOURNAMENT_PARTICIPANT_ROLE_NAME:
                participant_role = r

        team_role = await ctx.message.guild.create_role(
            name=team_name_for_role, mentionable=True
        )
        fc_role = await ctx.message.guild.create_role(name=friend_code)

        await ctx.message.author.add_roles(participant_role, team_role, fc_role)

        await ctx.send(
            f"All done. Enjoy the tournament and don't forget to check-in from 1 hour before the tournament starts!"
        )

    @commands.command(name="tourneymaps")
    @commands.is_owner()
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
        # Winners includes grand finals + bracket reset
        winner_map_amount = ceil(L2) + 1
        loser_map_amount = ceil(L2) + ceil(log(L2, 2))

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

        mode_emoji = f"{modes_to_emoji['Splat Zones']} "
        before_all = (
            f"Mode: {mode_emoji}Splat Zones\n\n"
            if ruleset.upper() in ["ITZ", "DRAFT"]
            else ""
        )
        for line in split_to_shorter_parts(
            before_all + winner_map_str + losers_map_str
        ):
            await ctx.send(line)


def setup(bot):
    bot.add_cog(TournamentCog(bot))
