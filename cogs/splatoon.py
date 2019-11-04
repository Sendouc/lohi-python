import discord
from discord.ext import commands
import time

from .utils.lists import (
    maps,
    map_part_to_full,
    mode_part_to_full,
    modes_to_emoji,
    weapons_to_emoji,
)
from .utils.classes.LohiEmbed import LohiEmbed
from .utils.helper import get_close_weapon, split_to_shorter_parts
from .utils.map_generator import map_generation


class SplatoonCog(commands.Cog, name="Splatoon"):
    def __init__(self, bot):
        self.bot = bot

    def get_rotation_lines(self, ok_maps: set, ok_modes: set, rotations: list) -> str:
        game_mode = rotations[0]["game_mode"]["name"]
        to_be_returned = [f"{modes_to_emoji[game_mode]} `{game_mode}`\n\n"]
        rotation_count = 4
        for r in rotations:
            mode = r["rule"]["name"]
            if mode not in ok_modes and len(ok_modes) != 0:
                continue
            map_1 = r["stage_a"]["name"]
            map_2 = r["stage_b"]["name"]
            if (map_1 not in ok_maps and map_2 not in ok_maps) and len(ok_maps) != 0:
                continue

            start_time = r["start_time"]
            end_time = r["end_time"]
            current_time = int(time.time())
            if end_time < current_time:
                continue
            if start_time < current_time:
                time_in_seconds = end_time - current_time
                # For it to work on Windows - needs to be replaced by #
                time_string = time.strftime(
                    "**%-Hh %-Mmin left**\n", time.gmtime(time_in_seconds)
                )
            else:
                time_in_seconds = start_time - current_time
                time_string = time.strftime(
                    "**In %-Hh %-Mmin**\n", time.gmtime(time_in_seconds)
                )
            to_be_returned.append(time_string)

            to_be_returned.append(f"{modes_to_emoji[mode]} {map_1} & {map_2}\n\n")
            rotation_count -= 1
            if rotation_count == 0:
                break

        # If filter was so strict no rotations matching could be found
        if rotation_count == 4:
            to_be_returned.append("No rotations found\n\n")

        return "".join(to_be_returned)

    @commands.command(name="rot")
    async def display_rotation(self, ctx, *maps_or_modes):
        """
        Displays the rotation with optional parameters to 
        filter the result. Example usage: .rot sz reef
        Data provided by splatoon2.ink
        """
        to_be_said_parts = ["> Filters applied: "]
        ok_maps = set()
        ok_modes = set()
        for m in maps_or_modes:
            m_lower = m.lower()
            if m_lower in map_part_to_full:
                ok_maps.add(map_part_to_full[m_lower])
            elif m_lower in mode_part_to_full:
                ok_modes.add(mode_part_to_full[m_lower])
            else:
                return await ctx.send(
                    "Unfortunately I'm not sure what"
                    f" map or mode '{m}' is referring to, {ctx.message.author.name}"
                )
        rotation_data = await self.bot.api.get_rotation_data()
        if "Turf War" in ok_modes:
            return await ctx.send("Scrim Bunker Games hard!")
        else:
            for mode in ok_modes:
                to_be_said_parts.append(f"{mode}, ")
            for stage in ok_maps:
                to_be_said_parts.append(f"{stage}, ")

            if len(ok_maps) + len(ok_modes) == 0:
                del to_be_said_parts[0]
            else:
                # Remove ", " from the last item
                to_be_said_parts[-1] = to_be_said_parts[-1][:-2]
            to_be_said_parts.append("\n")
            to_be_said_parts.append(
                self.get_rotation_lines(ok_maps, ok_modes, rotation_data["gachi"])
            )
            to_be_said_parts.append(
                self.get_rotation_lines(ok_maps, ok_modes, rotation_data["league"])
            )

        await ctx.send("".join(to_be_said_parts))

    @commands.command(name="sr")
    async def display_salmon_run_schedule(self, ctx):
        """
        Displays the Salmon Run shift schedule.
        Data provided by splatoon2.ink
        """
        sr_data = await self.bot.api.get_salmon_run_data()
        to_be_said = "<:grizz:622769856248283136> `Salmon Run`\n\n"
        for rot in sr_data["details"]:
            start_time = rot["start_time"]
            end_time = rot["end_time"]
            current_time = int(time.time())
            if end_time < current_time:
                continue
            if start_time < current_time:
                time_in_seconds = end_time - current_time
                if time_in_seconds < 86400:
                    # For it to work on Windows - needs to be replaced by #
                    time_string = time.strftime(
                        "**%-H hours %-M minutes left** \n",
                        time.gmtime(time_in_seconds),
                    )
                else:
                    time_string = time.strftime(
                        "** %-d days %-H hours %-M minutes left** \n",
                        time.gmtime(time_in_seconds),
                    )
            else:
                time_in_seconds = start_time - current_time
                if time_in_seconds < 86400:
                    time_string = time.strftime(
                        "**In %-H hours %-M minutes** \n", time.gmtime(time_in_seconds)
                    )
                else:
                    time_string = time.strftime(
                        "**In %-d days %-H hours %-M minutes** \n",
                        time.gmtime(time_in_seconds),
                    )
            if "1 days" in time_string:
                time_string = time_string.replace("days", "day")
            if " 1 hours" in time_string:
                time_string = time_string.replace("hours", "hour")
            if " 1 minutes" in time_string:
                time_string = time_string.replace("minutes", "minute")
            to_be_said += time_string

            for w in rot["weapons"]:
                # TODO: Add the other kind of question mark
                if "weapon" in w:
                    to_be_said += weapons_to_emoji.get(w["weapon"]["name"])
                else:
                    to_be_said += "<:Unknown:611199200788611079>"

            to_be_said += f' {rot["stage"]["name"]}\n\n'

        await ctx.send(to_be_said)

    # TODO: Make 10 builds per page - needs change on the API
    @commands.command(name="wbuilds")
    async def display_builds_of_weapon(self, ctx, *weapon_and_page):
        """
        Searchs for builds with the given weapon.
        Example usage: .wbuilds Tenta Brella
        Special arguments:
        [(number)] - Shows the page corresponding the number
        top500 - Shows top500 builds only
        """
        page = 1
        top500 = False

        weapon_parts = []
        for arg in weapon_and_page:
            if "(" in arg and ")" in arg:
                try:
                    page = int(arg.replace("(", "").replace(")", ""))
                    continue
                except ValueError:
                    return await ctx.send(
                        f"Expected `{arg}` to be a number since it was wrapped in ( ) but it wasn't..."
                    )

            if arg.upper() == "TOP500":
                top500 = True
                continue

            weapon_parts.append(arg)

        weapon_parts_joined = " ".join(weapon_parts)
        weapon = get_close_weapon(weapon_parts_joined)
        if weapon is None:
            return await ctx.send(
                f"Sorry I'm not sure what weapon `{weapon_parts_joined}` is referring to..."
            )

        builds_dict = await self.bot.api.get_builds(weapon=weapon, page=page)
        if builds_dict is None:
            return await ctx.send(f"{weapon} doesn't have {page} pages...")
        wpn_emoji = weapons_to_emoji[weapon]
        page_count = builds_dict["pageCount"]
        # TODO: See below.
        footer = "\uFEFF"
        if not top500:
            footer = f"Page {page}/{page_count}"
        builds_embed = LohiEmbed(
            title=f"{wpn_emoji} {weapon} Builds",
            url=f"https://sendou.ink/builds/{weapon.replace(' ', '_')}",
            footer=footer,
        )
        builds_embed.add_weapon_build_fields(builds_dict["builds"], top500_only=top500)

        for e in builds_embed.get_embeds():
            await ctx.send(embed=e)

        # TODO: Basically this is a bit bad since if there are over 20 Top 500 builds the user won't know there is another page
        # to view but this isn't a problem that can occur just yet.
        if page_count > page and not top500:
            await ctx.send(
                f"Use the command `.wbuilds {weapon_parts_joined} ({page+1})` to view the next page."
            )

    @commands.command(name="maps")
    async def generate_maplist_for_scrims(self, ctx, *options):
        """
        Get a maplist to scrim on using a maplist of your choice.
        Special arguments:
        [(number)] - Amount of maps to generate
        [name of maplist] - Default is this month's ranked
        pretty - Different formatting with emoji
        """
        maplists = await self.bot.api.get_maplists()
        amount_to_generate = 20
        pretty = False
        maplist_names = []
        for maplist in maplists:
            maplist_names.append(maplist["name"])

        maplist_to_use = maplists[0]  # Default is ranked
        for option in options:
            if "(" in option and ")" in option:
                try:
                    amount_to_generate = int(option.replace("(", "").replace(")", ""))
                    if 1 > amount_to_generate or amount_to_generate > 50:
                        return await ctx.send(
                            "Amount of maps to generate has to be between 1 and 50."
                        )
                    continue
                except ValueError:
                    return await ctx.send(
                        f"Expected *{option}* to be a number since it was wrapped in ( ) but it wasn't..."
                    )
            else:
                found_maplist = False
                if option.upper() == "PRETTY":
                    pretty = True
                    continue
                for index, name in enumerate(maplist_names):
                    if option.upper() in name.upper().split(" "):
                        maplist_to_use = maplists[index]
                        found_maplist = True
                        break
                if not found_maplist:
                    maplist_names = "\n".join(maplist_names)
                    return await ctx.send(
                        f"Sorry not sure what map pool *{option}* is referring to. Available map pools:\n{maplist_names}"
                    )

        maplist_name = maplist_to_use.pop("name")
        generated_maps = map_generation(
            map_pool=maplist_to_use, games=[amount_to_generate]
        )

        to_say = f"> Map pool used: {maplist_name}\n"
        if not pretty:
            to_say += "```"
        map_number = 1
        for mode, stage in generated_maps[0]:
            if pretty:
                to_say += f"{map_number}) {modes_to_emoji[mode_part_to_full[mode]]} on `{stage}`\n"
            else:
                to_say += f"{map_number}) {mode_part_to_full[mode]} on {stage}\n"
            map_number += 1
        if not pretty:
            to_say += "```"
        if len(to_say) > 2000:
            return await ctx.send(
                f"This maplist is too strong... (length was {len(to_say)} when the max is 2000)"
            )
        await ctx.send(to_say)

    @commands.command(name="pool")
    async def display_map_pool(self, ctx, *arguments):
        """
        Shows the map belonging to the map pool.
        Calling without arguments shows all the available
        map pools.
        Special arguments:
        compact - Doesn't show maps not part of the pool.
        """
        NO_EMOJI = " " * 6
        maplists = await self.bot.api.get_maplists()
        maplist_names = []
        compact = False
        for maplist in maplists:
            maplist_names.append(maplist["name"])

        maplist_to_use = None
        for arg in arguments:
            if arg.upper() == "COMPACT":
                compact = True
                continue
            for index, name in enumerate(maplist_names):
                if arg.upper() in name.upper().split(" "):
                    maplist_to_use = maplists[index]
                    break
        if not maplist_to_use:
            maplist_names = "\n".join(maplist_names)
            return await ctx.send(f"Available map pools:\n{maplist_names}")

        to_say = f"> Map pool: {maplist_to_use['name']}\n"
        for m in maps:
            emojis = [NO_EMOJI] * 4
            for index, mode in enumerate(("sz", "tc", "rm", "cb")):
                if m in maplist_to_use[mode]:
                    emojis[index] = modes_to_emoji[mode_part_to_full[mode]]
            if emojis != [NO_EMOJI] * 4 or not compact:
                to_say += f"{emojis[0]}|{emojis[1]}|{emojis[2]}|{emojis[3]} - `{m}`\n"
        for msg in split_to_shorter_parts(to_say):
            await ctx.send(msg)


def setup(bot):
    bot.add_cog(SplatoonCog(bot))
