import discord
from discord.ext import commands
import asyncio
import challonge
import re
from math import log, ceil

from .utils import ids
from .utils import config
from .utils.map_generator import map_generation
from .utils.lists import maps, modes_to_emoji, itz_map_votes
from .utils.helper import split_to_shorter_parts

TOURNAMENT_URL = "InTheZone15"
TOURNAMENT_PARTICIPANT_ROLE_NAME = "Registered"
REGISTERED_ROLE_ID = 409130904418516994
CHECKED_IN_ROLE_ID = 692878166070394950


class TournamentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checkin_open = False

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
        Example usage: .roles "Team Olive" 0109-3838-9398
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

        found_name = found_name[:50]

        team_name_for_role = f"{found_name} 🏆"

        matched = re.match(r"^[0-9]{4}-[0-9]{4}-[0-9]{4}$", friend_code)

        if not bool(matched):
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
            f"All done. Thank you for registering. Don't forget the check-in that begins 1 hour before the tournament is scheduled to start!"
        )

    @commands.command(name="checkin")
    @commands.has_role("Registered")
    async def check_in_for_tournament(self, ctx):
        if not self.checkin_open:
            return await ctx.send("Check-in is not open yet")
        registered_role = ctx.message.guild.get_role(REGISTERED_ROLE_ID)
        checked_in_role = ctx.message.guild.get_role(CHECKED_IN_ROLE_ID)
        await ctx.message.author.add_roles(checked_in_role)
        await ctx.message.author.remove_roles(registered_role)
        await ctx.message.add_reaction("✅")

    @commands.command(name="togglecheckin")
    @commands.has_role("Staff")
    async def toggle_check_in_bool(self, ctx):
        self.checkin_open = not self.checkin_open
        if not self.checkin_open:
            await ctx.send("Check-in is now closed")
        else:
            await ctx.send("Check-in is now open")

    @commands.command(name="checkedin")
    @commands.has_role("Staff")
    async def toggle_check_in_bool(self, ctx):
        user = await challonge.get_user(
            config.CHALLONGE_ACCOUNT_NAME, config.CHALLONGE_TOKEN
        )
        tournament = await user.get_tournament(url=TOURNAMENT_URL, subdomain="sendous")
        participants = await tournament.get_participants()
        checked_in_teams = []
        registered_teams = []
        no_role_teams = []
        not_on_challonge_teams = []
        left_server = []
        checked_in_role = ctx.message.guild.get_role(CHECKED_IN_ROLE_ID)
        registered_role = ctx.message.guild.get_role(REGISTERED_ROLE_ID)

        guild_roles = ctx.message.guild.roles

        for participant in participants:
            team_name = " ".join(participant.display_name.split())
            role_name = f"{team_name} 🏆"

            found = False
            for r in guild_roles:

                if r.name == role_name:
                    if len(r.members) == 0:
                        left_server.append(role_name)
                        found = True
                    else:
                        for users_role in r.members[0].roles:
                            if users_role.id == REGISTERED_ROLE_ID:
                                registered_teams.append(team_name)
                                found = True
                                continue
                            elif users_role.id == CHECKED_IN_ROLE_ID:
                                checked_in_teams.append(team_name)
                                found = True
                                continue

                if found:
                    break

            if not found:
                no_role_teams.append(team_name)

        for r in guild_roles:
            if "🏆" in r.name:
                team_name = " ".join(r.name.replace(" 🏆", "").split())

            if (
                team_name not in checked_in_teams
                and team_name not in registered_teams
                and team_name not in no_role_teams
                and team_name not in left_server
            ):
                not_on_challonge_teams.append(team_name)

        to_be_said = []

        if len(checked_in_teams) > 0:
            to_be_said.append(f"✅ **Checked in ({len(checked_in_teams)})**")
            to_be_said.append("\n".join(checked_in_teams))

        if len(registered_teams) > 0:
            to_be_said.append(
                f"\n⚠️ **Has registered roles ({len(registered_teams)})**"
            )
            to_be_said.append("\n".join(registered_teams))

        if len(no_role_teams) > 0:
            to_be_said.append(
                f"\n❌ **Registered on challonge but claimed no roles ({len(no_role_teams)})**"
            )
            to_be_said.append("\n".join(no_role_teams))

        if len(not_on_challonge_teams) > 0:
            to_be_said.append(
                f"\n❓ **Has roles but changed name on Challonge ({len(not_on_challonge_teams)})**"
            )
            to_be_said.append("\n".join(not_on_challonge_teams))

        if len(left_server) > 0:
            to_be_said.append(f"\n👻 **Left server ({len(left_server)})**")
            to_be_said.append("\n".join(left_server))

        to_be_said.append(f"\n\n*{len(participants)} teams on Challonge*")

        await ctx.send("\n".join(to_be_said))

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
            map_pool=events[ruleset]["map_pool"],
            games=games,
            popularity={"sz": itz_map_votes},
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
