import discord
from discord.ext import commands
import random
import typing

from .utils import ids
from .utils.lists import weapons, adjectives
from .utils.helper import split_to_shorter_parts

class MiscCog(commands.Cog, name="Misc"):
    def __init__(self, bot):
        self.bot = bot
    
    async def is_in_sendou_server(ctx):
        return (ctx.message.guild and ctx.message.guild.id == ids.SENDOU_SERVER_ID) or ctx.message.author.id == ids.OWNER_ID
    
    async def is_in_plusone(ctx):
        return (ctx.message.guild and ctx.message.guild.id == ids.PLUSONE_SERVER_ID) or ctx.message.author.id == ids.OWNER_ID

    async def can_create_color_roles(ctx):
        if not ctx.message.guild:
            return False
            
        if ctx.message.guild.id == ids.PLUSONE_SERVER_ID:
            return True

        if ctx.message.guild.id == ids.SENDOU_SERVER_ID:
            for role in ctx.message.author.roles:
                if role.name in ["Twitch Subscriber", "Staff", "Nitro Booster"]:
                    return True
            return False

        return False

    @commands.command()
    async def ping(self, ctx):
        '''
        Bot's latency. Normally below 200ms.
        '''
        ping = round(self.bot.latency * 1000)
        await ctx.send(f'My ping is {ping}ms')

    @commands.command(name='give')
    @commands.check(is_in_sendou_server)
    async def give_or_remove_role(self, ctx, role : typing.Optional[discord.Role] = None):
        '''
        Gives or takes away a role (case sensitive).
        Use !give to view all the roles that are available.
        '''
        roles_available = ['Tournament', 'Content', 'Jury']

        if not role:
            roles_string = "\n".join(roles_available)
            return await ctx.send(f'Roles available:\n{roles_string}')

        if role.name not in roles_available:
            return await ctx.send('That role isn\'t available. Use `.give` to get a list of all the available roles')

        if role in ctx.message.author.roles:
            await ctx.message.author.remove_roles(role)
            return await ctx.send(f'{role.name} succesfully removed from {ctx.message.author.name}')
        
        await ctx.message.author.add_roles(role)
        await ctx.send(f'{role.name} succesfully added to {ctx.message.author.name}')

    @commands.command(name='color')
    @commands.check(can_create_color_roles)
    async def give_or_edit_color_role(self, ctx, color : typing.Optional[discord.Color] = None, *role_name):
        '''
        Gives or modifies a color role. 
        Example usage: !color #6A7E25 my cool role name
        '''
        if not color:
            return await ctx.send('Valid color not provided. Example usage: `.color #6A7E25`')

        if len(role_name) == 0:
            name = ctx.message.author.name
        else:
            name = " ".join(role_name)

        if len(name) > 50:
            return await ctx.send(f'Max character count for the role to be given is 50. The name for the role you gave was {len(name)} characters long')

        for role in ctx.message.author.roles:
            if '!' in role.name:
                await role.edit(name=f'{name}!', color=color)
                return await ctx.send(f'Edited the role, {ctx.message.author.name}!')

        created_role = await ctx.message.guild.create_role(name=f'{name}!', color=color)
        await ctx.message.author.add_roles(created_role)
        await ctx.send(f'Enjoy your new color, {ctx.message.author.name}!')
    
    def discord_tag_or_nickname(self, member: discord.Member) -> str:
        nickname = ids.ALIASES.get(member.id)
        if nickname:
            return f"`{member} ({nickname}) <@{member.id}>`\n"
        return f"`{member} <@{member.id}>`\n"

    @commands.command(name='plusone')
    @commands.check(is_in_plusone)
    async def display_members_for_voting(self, ctx):
        '''
        Displays the relevant members in +1 in a format
        usable for voting.
        '''
        SUGGEST_LIMIT = 11
        to_be_said = "> Members\n"
        plus_one = self.bot.get_guild(ids.PLUSONE_SERVER_ID)
        excluded_from_voting = 0
        vouches = []
        ids_included = set()
        
        for m in sorted(plus_one.members, key=lambda x: x.name.lower()):
            if m.id in ids.TO_EXCLUDE_FROM_VOTING:
                excluded_from_voting += 1
                continue
            is_vouch = False
            for r in m.roles:
                if r.name == "Vouch":
                    vouches.append(m)
                    is_vouch = True
                    continue
            if is_vouch:
                continue
            to_be_said += self.discord_tag_or_nickname(m)
            ids_included.add(m.id)
        to_be_said += "> Vouches\n"

        for m in vouches:
            to_be_said += self.discord_tag_or_nickname(m)
            ids_included.add(m.id)
        to_be_said += "> Suggested eligible for voting\n"

        suggest_ch = self.bot.get_channel(ids.PLUSONE_SUGGEST_CHANNEL_ID)
        for m in await suggest_ch.history().flatten():
            for r in m.reactions:
                if r.emoji == "👍" and r.count >= SUGGEST_LIMIT:
                    for e in m.embeds:
                        user_id = int(e.footer.text)
                        if user_id in ids_included:
                            break
                        user_name = e.title.split("User Suggestion: ")[1]
                        to_be_said += f"`{user_name} [*] <@{user_id}>`\n"

        to_be_said += f"\n{len(plus_one.members)} members in the server ({excluded_from_voting} excluded from voting)"
        for msg in split_to_shorter_parts(to_be_said):
            await ctx.send(msg)

        # TODO: NA/EU count

    @commands.command(name='whoami')
    async def tell_them_how_it_is(self, ctx):
        '''
        Learn something about yourself.
        '''
        did = ctx.message.author.id
        random.seed(did)
        adjective = random.choice(adjectives)
        random.seed(did)
        weapon = random.choice(weapons)
        await ctx.send(f'{adjective.capitalize()} {weapon} main. That is who you are, {ctx.message.author.name}')

def setup(bot):
    bot.add_cog(MiscCog(bot))