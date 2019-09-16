import discord
from discord.ext import commands
import time

from .utils.lists import map_part_to_full, mode_part_to_full, modes_to_emoji, weapons_to_emoji

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
                time_string = time.strftime("**%-Hh %Mmin left**\n", time.gmtime(time_in_seconds))
            else:
                time_in_seconds = start_time - current_time
                time_string = time.strftime("**In %-Hh %Mmin**\n", time.gmtime(time_in_seconds))
            to_be_returned.append(time_string)

            to_be_returned.append(f"{modes_to_emoji[mode]} {map_1} & {map_2}\n\n")
            rotation_count -= 1
            if rotation_count == 0:
                break
        
        # If filter was so strict no rotations matching could be found
        if rotation_count == 4:
            to_be_returned.append("No rotations found\n\n")
        
        return "".join(to_be_returned)

    @commands.command(name='rot')
    async def display_rotation(self, ctx, *maps_or_modes):
        '''
        Displays the rotation with optional parameters to 
        filter the result. Example usage: .rot sz reef
        Data provided by splatoon2.ink
        '''
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
                return await ctx.send("Unfortunately I'm not sure what" 
                f" map or mode '{m}' is referring to, {ctx.message.author.name}")
        rotation_data = await self.bot.api.get_rotation_data()
        if "Turf War" in ok_modes:
            return await ctx.send("Adding Turf tomorrow lol until then scrim Bunker Games hard")
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
            to_be_said_parts.append(self.get_rotation_lines(ok_maps, ok_modes, rotation_data["gachi"]))
            to_be_said_parts.append(self.get_rotation_lines(ok_maps, ok_modes, rotation_data["league"]))

        await ctx.send("".join(to_be_said_parts))

    @commands.command(name='sr')
    async def display_salmon_run_schedule(self, ctx):
        '''
        Displays the Salmon Run shift schedule.
        Data provided by splatoon2.ink
        '''
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
                # For it to work on Windows - needs to be replaced by #
                time_string = time.strftime("** %-d days %-H hours %M minutes left** \n", time.gmtime(time_in_seconds))
            else:
                time_in_seconds = start_time - current_time
                time_string = time.strftime("**In %-d days %-H hours %M minutes** \n", time.gmtime(time_in_seconds))
            if "1 days" in time_string:
                time_string = time_string.replace("days", "day")
            if " 1 hours" in time_string:
                time_string = time_string.replace("hours", "hour")
            if " 1 minutes" in time_string:
                time_string = time_string.replace("minutes", "minute")
            to_be_said += time_string

            for w in rot["weapons"]:
                # TODO: Add the other kind of question mark
                to_be_said += weapons_to_emoji.get(w["weapon"]["name"], "<:Unknown:611199200788611079>")
            
            to_be_said += f' {rot["stage"]["name"]}\n\n'

        await ctx.send(to_be_said)

def setup(bot):
    bot.add_cog(SplatoonCog(bot))