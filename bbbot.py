from dotenv import load_dotenv
from discord.utils import get, find
from discord.ext import commands
import os

import codenames

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')


# create a game
@bot.command(name='codenames')
async def start(ctx):
    response = codenames.create_game()
    await ctx.send(response)


# player guess
@bot.command(name='guess')
@commands.has_any_role('Blue Team', 'Red Team')
async def guess(ctx, word):
    user = ctx.message.author
    spymaster = None
    is_red = find(lambda r: r.name == 'Red Team', ctx.message.guild.roles)
    is_blue = find(lambda r: r.name == 'Blue Team', ctx.message.guild.roles)
    is_red_sm = find(
        lambda r: r.name == 'Red Spymaster', ctx.message.guild.roles)
    is_blue_sm = find(
        lambda r: r.name == 'Blue Spymaster', ctx.message.guild.roles)

    # make sure two spymasters exist
    no_blue_sm = True
    no_red_sm = True
    for member in ctx.guild.members:
        if is_blue_sm in member.roles:
            no_blue_sm = False
        if is_red_sm in member.roles:
            no_red_sm = False
    if no_blue_sm or no_red_sm:
        await ctx.send("Requires 2 Spymasters to begin.")
        return

    # determine guesser team
    if is_red in user.roles:
        team = 'Red Team'
    elif is_blue in user.roles:
        team = 'Blue Team'

    # check if correct team guessing and guesses left > 0
    if codenames.get_turn() == team and codenames.get_guesses() != 0:
        await ctx.send(codenames.player_guess(word, team))
        codenames.set_guesses(int(codenames.get_guesses())-1)
        await ctx.send("Clue is " + codenames.get_clue() + ". " +
                       str(codenames.get_guesses()) + " guesses remaining.")
    else:
        await ctx.send("Not your team's turn.")

    # update spymaster logic
    response = "Your remaining words: " + str(codenames.update_spymaster(team))
    if team == 'Red Team':
        to_check = is_red_sm
    elif team == 'Blue Team':
        to_check = is_blue_sm

    for member in ctx.guild.members:
        if to_check in member.roles:
            spymaster = member
    await spymaster.send(response)


# assign roles
@bot.command(name='join')
async def add_role(ctx, color, role):
    team = color + " " + role
    user = ctx.message.author
    is_red = find(lambda r: r.name == 'Red Team', ctx.message.guild.roles)
    is_blue = find(lambda r: r.name == 'Blue Team', ctx.message.guild.roles)
    is_red_sm = find(
        lambda r: r.name == 'Red Spymaster', ctx.message.guild.roles)
    is_blue_sm = find(
        lambda r: r.name == 'Blue Spymaster', ctx.message.guild.roles)

    # ensure one spymaster per color
    if role == "Spymaster":
        for member in ctx.guild.members:
            if color == 'Blue':
                if is_blue_sm in member.roles:
                    await ctx.send("There is a spymaster of that color.")
                    return
            elif color == 'Red':
                if is_red_sm in member.roles:
                    await ctx.send("There is a spymaster of that color.")
                    return

    # check if player is already on a team
    if is_red in user.roles or is_blue in user.roles:
        await ctx.send("Already on a team.")
        return

    # check if player is spymaster
    if is_red_sm in user.roles or is_blue_sm in user.roles:
        await ctx.send("Cannot join team as Spymaster.")
        return

    # add role
    if team == 'Blue Team' or 'Red Team':
        await user.add_roles(get(user.guild.roles, name=team))
        await ctx.send("Joined " + team + ".")
    else:
        await ctx.send("Not a valid team.")


# leave team
@bot.command(name='leave')
async def remove_role(ctx, color, role):
    team = color + " " + role
    user = ctx.message.author
    role = find(lambda r: r.name == team, ctx.message.guild.roles)

    # check if actually on team
    if role not in user.roles:
        await ctx.send("Not on that team.")
        return

    # remove role
    if team == 'Blue Team' or 'Red Team':
        await user.remove_roles(get(user.guild.roles, name=team))
        await ctx.send("Left " + team + ".")
    else:
        await ctx.send("Not a valid team.")


# give clue
@bot.command(name='clue')
@commands.has_any_role('Blue Spymaster', 'Red Spymaster')
async def clue(ctx, word, number):
    codenames.set_guesses(number)
    codenames.set_clue(word)
    await ctx.send("Clue is " + word + ". " + number + " guesses remaining.")


# pass
@bot.command(name='pass')
@commands.has_any_role('Blue Team', 'Red Team')
async def pass_turn(ctx):
    user = ctx.message.author
    is_red = find(lambda r: r.name == 'Red Team', ctx.message.guild.roles)
    is_blue = find(lambda r: r.name == 'Blue Team', ctx.message.guild.roles)

    # determine guesser team
    if is_red in user.roles:
        team = 'Red Team'
    elif is_blue in user.roles:
        team = 'Blue Team'

    if codenames.get_turn() == team:
        codenames.set_clue("")
        codenames.set_guesses(0)
        await ctx.send(team + " has passed their turn.")
    else:
        await ctx.send("Not your turn.")


# command for testing
@bot.command(name='give')
async def test(ctx, word):
    if word == 'head':
        await ctx.send('Shaheen is fascist.')    
    else:
        await ctx.send('Shaheen is FASCIST I SAID.')


bot.run(TOKEN)
