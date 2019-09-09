import discord
from discord.ext import commands
import random
import typing

from .utils import ids
from .utils.lists import weapons, adjectives

class MiscCog(commands.Cog, name="Misc"):
    def __init__(self, bot):
        self.bot = bot
    
    async def is_in_sendou_server(ctx):
        can_be_sent = ctx.message.guild.id == ids.SENDOU_SERVER_ID
        if not can_be_sent:
            await ctx.send('This command can only be used in the "Sendou" server.')
        
        return can_be_sent

    async def can_create_color_roles(ctx):
        if ctx.message.guild.id == ids.PLUSONE_SERVER_ID:
            return True

        if ctx.message.guild.id == ids.SENDOU_SERVER_ID:
            for role in ctx.message.author.roles:
                if role.name in ["Twitch Subscriber", "Staff", "Nitro Booster"]:
                    return True
            await ctx.send("This command can only be used by Twitch subscribers or Nitro Boosters.")
            return False

        await ctx.send("This command can't be used in this server.")
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
            return await ctx.send('That role isn\'t available. Use `.give` to get a list of all the available roles.')

        if role in ctx.message.author.roles:
            await ctx.message.author.remove_roles(role)
            return await ctx.send(f'{role.name} succesfully removed from {ctx.message.author.name}.')
        
        await ctx.message.author.add_roles(role)
        await ctx.send(f'{role.name} succesfully added to {ctx.message.author.name}.')

    @commands.command(name='color')
    @commands.check(can_create_color_roles)
    async def give_or_edit_color_role(self, ctx, color : typing.Optional[discord.Color] = None, *args):
        '''
        Gives or modifies a color role. 
        Example usage: !color #6A7E25 my cool role name
        '''
        if not color:
            return await ctx.send('Valid color not provided. Example usage: `.color #6A7E25`')

        if len(args) == 0:
            name = ctx.message.author.name
        else:
            name = " ".join(args)

        if len(name) > 50:
            return await ctx.send(f'Max character count for the role to be given is 50. The name for the role you gave was {len(name)} characters long.')

        for role in ctx.message.author.roles:
            if '!' in role.name:
                await role.edit(name=f'{name}!', color=color)
                return await ctx.send(f'Edited the role, {ctx.message.author.name}!')

        created_role = await ctx.message.guild.create_role(name=f'{name}!', color=color)
        await ctx.message.author.add_roles(created_role)
        await ctx.send(f'Enjoy your new color, {ctx.message.author.name}!')

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
        await ctx.send(f'{adjective.capitalize()} {weapon} main. That is who you are, {ctx.message.author.name}.')

def setup(bot):
    bot.add_cog(MiscCog(bot))