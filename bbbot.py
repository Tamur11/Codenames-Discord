import os
from io import BytesIO

import discord
from discord.ext import commands
from discord.utils import get, find
from dotenv import load_dotenv

from games.game import Game
from games.codenames import Codenames
from games.werewolf import Werewolf

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

current_game = Game()  # variable to hold the current game being played


async def test_current_game(ctx, intended_game) -> bool:
    if current_game.__class__ == intended_game:
        return True
    else:
        return False


# error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send("Not a valid command!")
        return
    elif isinstance(
            error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("Command missing an argument!")
        return
    elif isinstance(error, discord.ext.commands.errors.CommandError):
        await ctx.send("Error with command!")
    else:
        return


# create a werewolf game
@bot.command(name='werewolf')
async def werewolf(ctx):
    global current_game
    current_game = Werewolf()

    await ctx.send("One Night Ultimate Werewolf game started!")


# werewolf add role card
@bot.command(name='add')
async def add_role(ctx, role):
    valid_roles = [
        'villager',  # up to 3
        'werewolf',  # up to 2
        'seer',
        'robber',
        'troublemaker',
        'tanner',
        'drunk',
        'hunter',
        'mason',  # always add 2
        'insomniac',
        'minion',
        'doppelganger'
    ]

    if role != 'villager' and role != 'werewolf' and role != 'mason' and\
            role in current_game.get_role_list():
        await ctx.send(role.title() + " has already been added.")
        return
    elif role != 'villager' and current_game.get_role_list().count(role) >= 2:
        await ctx.send("Already have 2 " + role + " added.")
        return
    elif current_game.get_role_list().count(role) >= 3:
        await ctx.send("Already have 3 villagers added.")
        return

    if role.lower() in valid_roles:
        if role == 'mason':
            current_game.add_role(role)
            current_game.add_role(role)
        else:
            current_game.add_role(role)

        role_list_str = ''
        dupe = []
        for role in current_game.get_role_list():
            if current_game.get_role_list().count(role) > 1 and\
                    role not in dupe:
                role_list_str += role.title() + ' (' +\
                    str(current_game.get_role_list().count(role)) + ')\n'
                dupe.append(role)
            elif role not in dupe:
                role_list_str += role.title() + '\n'
        await ctx.send("Added " + role +
                       " to current Werewolf game.\nCurrent roster:\n" +
                       role_list_str)

        # check how many roles remaining
        await roles_remain(ctx)


# roles to add/remove before can start
async def roles_remain(ctx):
    diff = len(current_game.get_role_list())-3 -\
        len(current_game.get_players())
    if diff == 0:
        await ctx.send("Good to go! Type !start to begin the night...")
        return
    elif diff > 0:
        await ctx.send(str(diff) + " too many roles.")
        return
    else:
        await ctx.send("Need " + str(abs(diff)) + " more roles.")
        return


# run the night logic part of the game
async def night_logic(ctx):
    current_game.assign_roles()
    await ctx.send("The most pythonic line ever returns: " +
                   str(current_game.get_players()))


# create a codenames game
@bot.command(name='codenames')
async def codenames(ctx):
    global current_game
    current_game = Codenames()

    await ctx.send('Codenames game started! Add both spymasters to "!start"')


# start a game
@bot.command(name='start')
async def start(ctx):
    # ww start logic
    if await test_current_game(ctx, Werewolf):
        # check if at least 3 players
        # if len(current_game.get_players()) < 3:
        #     current_players = "Current players:\n"
        #     for user in current_game.get_players():
        #         current_players += user.display_name + '\n'
        #     await ctx.send(
        #         "Must have at least 3 players to begin. Current players are:\n" +
        #         current_players)
        #     return

        # check if werewolf has been added
        if 'werewolf' not in current_game.get_role_list():
            await ctx.send("Must have at least one werewolf to begin.")
            return

        # check how many roles remaining
        await roles_remain(ctx)

        # run night logic
        await night_logic(ctx)

    # codenames start logic
    elif await test_current_game(ctx, Codenames):
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

        # start game logic
        current_game.set_started(True)
        await spymaster_words(ctx, 'Blue Team')
        await spymaster_words(ctx, 'Red Team')

        await send_image(ctx, None)
        await ping_roles(ctx)


# player guess
@bot.command(name='guess')
@commands.has_any_role('Blue Team', 'Red Team')
async def guess(ctx, word):
    global current_game
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    user = ctx.message.author
    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(ctx)

    # make sure two spymasters exist
    no_blue_sm = True
    no_red_sm = True
    for member in ctx.guild.members:
        if is_blue_sm in member.roles:
            no_blue_sm = False
        if is_red_sm in member.roles:
            no_red_sm = False
    if no_blue_sm or no_red_sm:
        await ctx.send("Requires 2 Spymasters to play.")
        return

    # determine guesser team
    if is_red in user.roles:
        team = 'Red Team'
    elif is_blue in user.roles:
        team = 'Blue Team'
    else:
        team = 'Error'

    # check if correct team guessing and guesses left > 0
    if current_game.get_turn() == team and current_game.get_guesses() != 0:
        response = current_game.player_guess(word.upper(), team)
        await ctx.send(response)
        # check if game should end
        if current_game.is_game_over() is not None:
            await send_image(ctx, None)
            await ctx.send("Game Over! " + current_game.is_game_over() +
                           ' wins! Type: "!codenames" to start a new game!')
            await clear_roles(ctx)
            current_game = Game()  # reset game
        # catch for typos
        if 'try again' in response:
            return
        # if guess was correct
        if response == 'Correct!':
            await send_image(ctx, None)
            if int(current_game.get_guesses()) == -2:
                await ctx.send(
                    "Your words are not related to " +
                    current_game.get_clue() +
                    ". You have infinite guesses remaining!")
            elif int(current_game.get_guesses()) == -3:
                await ctx.send(
                    "Clue is " + current_game.get_clue() +
                    ". You have infinite guesses remaining!")
            else:
                current_game.set_guesses(int(current_game.get_guesses()) - 1)
                await ctx.send(
                    "Clue is " + current_game.get_clue() + ". " +
                    str(current_game.get_guesses()) +
                    " guesses remaining.")

            if current_game.get_guesses() == 0:
                current_game.set_clue("")
                current_game.set_guesses(0)
                current_game.swap_turn()
                await spymaster_words(ctx, current_game.get_turn())
                await send_image(ctx, None)
                await ping_roles(ctx)
        # if guess was wrong
        elif 'Assassin' not in response:
            if team == 'Red Team':
                await ctx.send("Now Blue Spymaster's turn.")
                current_game.set_clue("")
                current_game.set_guesses(0)
                await spymaster_words(ctx, current_game.get_turn())
                await send_image(ctx, None)
                await ping_roles(ctx)
            elif team == 'Blue Team':
                await ctx.send("Now Red Spymaster's turn.")
                current_game.set_clue("")
                current_game.set_guesses(0)
                await spymaster_words(ctx, current_game.get_turn())
                await send_image(ctx, None)
                await ping_roles(ctx)
        # if assassin
        else:
            await clear_roles(ctx)
            current_game = Game()  # reset game
            return
    else:
        await ctx.send("Not your team's turn.")


async def color_tester(ctx):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    is_red = find(lambda r: r.name == 'Red Team', ctx.message.guild.roles)
    is_blue = find(lambda r: r.name == 'Blue Team', ctx.message.guild.roles)
    is_red_sm = find(
        lambda r: r.name == 'Red Spymaster', ctx.message.guild.roles)
    is_blue_sm = find(
        lambda r: r.name == 'Blue Spymaster', ctx.message.guild.roles)
    return is_blue, is_blue_sm, is_red, is_red_sm


# assign roles
@ bot.command(name='join')
async def join(ctx, *args):
    user = ctx.message.author

    # werewolf game check
    if not args and await test_current_game(ctx, Werewolf):
        if user not in current_game.get_players():
            current_game.add_players(user)
        else:
            await ctx.send("Already in game lobby.")
            return

        response = "Current players:\n"
        for user in current_game.get_players():
            response += user.display_name + '\n'
        await ctx.send(response)

        # check how many roles remaining
        await roles_remain(ctx)

    # codenames check
    elif await test_current_game(ctx, Codenames):
        color = args[0].title()
        role = args[1].title()
        team = color.title() + " " + role.title()

        is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(ctx)

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
            await ctx.send("Cannot join a team as Spymaster.")
            return

        # add spymaster role
        if team == 'Blue Spymaster' or team == 'Red Spymaster':
            await user.add_roles(get(user.guild.roles, name=team))
            # await send_image(user, team)
            await ctx.send("Joined " + team + ".")
            return

        # add team role
        if team == 'Blue Team' or team == 'Red Team':
            current_game.add_player(ctx.message.author.name, team)
            await user.add_roles(get(user.guild.roles, name=team))
            await ctx.send("Joined " + team + ".")
            return

        # catch typos
        await ctx.send(team + " is not a valid team.")
    else:
        return


# leave team
@ bot.command(name='leave')
async def remove_role(ctx, color, role):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    team = color.title() + " " + role.title()
    user = ctx.message.author
    role = find(lambda r: r.name == team, ctx.message.guild.roles)

    # check if actually on team
    if role not in user.roles:
        await ctx.send("Not on that team.")
        return

    # remove role
    if team == 'Blue Team' or team == 'Red Team':
        await user.remove_roles(get(user.guild.roles, name=team))
        await ctx.send("Left " + team + ".")
    elif (team == 'Blue Spymaster' or team == 'Red Spymaster') and\
            not current_game.get_started():
        await user.remove_roles(get(user.guild.roles, name=team))
        await ctx.send("Left " + team + ".")
    elif team == 'Blue Spymaster' or team == 'Red Spymaster' and\
            current_game.get_started():
        await ctx.send("Cannot leave spymaster once game has started.")
    else:
        await ctx.send("Not a valid team.")


# give clue
@ bot.command(name='clue')
@ commands.has_any_role('Blue Spymaster', 'Red Spymaster')
async def clue(ctx, *args):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    # make sure only one clue sent
    if current_game.get_clue():
        await ctx.send("A clue has already been given.")
        return

    # parse user input
    clue = '"'
    for arg in args:
        if arg.isdigit():
            number = arg
            clue = clue.strip() + '"'
            break
        else:
            clue += arg + ' '

    # make sure non-neg clue
    if int(number) < 0:
        await ctx.send("Number must be non-negative.")
        return

    user = ctx.message.author
    is_red_sm = find(
        lambda r: r.name == 'Red Spymaster', ctx.message.guild.roles)
    is_blue_sm = find(
        lambda r: r.name == 'Blue Spymaster', ctx.message.guild.roles)

    if is_red_sm in user.roles:
        spymaster_team = 'Red Team'
    elif is_blue_sm in user.roles:
        spymaster_team = 'Blue Team'
    else:
        spymaster_team = 'Error'

    if current_game.get_turn() != spymaster_team:
        await ctx.send("Not your team's turn.")
        return
    if number == '0':
        current_game.set_guesses(-2)
    elif number == '00':
        current_game.set_guesses(-3)
    else:
        current_game.set_guesses(int(number) + 1)
    current_game.set_clue(clue)
    if current_game.get_guesses() == -2:
        response = "Your words are not related to " + clue +\
            ". You have infinite guesses remaining!"
    elif current_game.get_guesses() == -3:
        response = "Clue is " + clue +\
            ". You have infinite guesses remaining!"
    else:
        response = "Clue is " + clue + ". " +\
            str(current_game.get_guesses()) + " guesses remaining."

    await ping_roles(ctx)
    clue_msg = await ctx.send(response)
    await clue_msg.pin()
    to_delete = await ctx.channel.history().next()
    await to_delete.delete()


# pass
@ bot.command(name='pass')
@ commands.has_any_role('Blue Team', 'Red Team')
async def pass_turn(ctx):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    user = ctx.message.author
    is_red = find(lambda r: r.name == 'Red Team', ctx.message.guild.roles)
    is_blue = find(lambda r: r.name == 'Blue Team', ctx.message.guild.roles)

    # determine guesser team
    if is_red in user.roles:
        team = 'Red Team'
    elif is_blue in user.roles:
        team = 'Blue Team'
    else:
        team = 'Error'

    if current_game.get_turn() == team:
        current_game.set_clue("")
        current_game.set_guesses(0)
        current_game.swap_turn()
        await spymaster_words(ctx, current_game.get_turn())
        await ctx.send(team + " has passed their turn.")
        await send_image(ctx, None)
        await ping_roles(ctx)
    else:
        await ctx.send("Not your turn.")


# display current turn
@bot.command(name='turn')
async def turn(ctx):
    # turn logic
    if current_game.get_clue() != '':
        await ctx.send(current_game.get_turn() + "'s turn.")
    elif current_game.get_clue() == '':
        if current_game.get_turn() == 'Blue Team':
            await ctx.send("Blue Spymaster's turn.")
        elif current_game.get_turn() == 'Red Team':
            await ctx.send("Red Spymaster's turn.")


# display which team's turn
@bot.command(name='teams')
async def info(ctx):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(ctx)
    # num people and names on each team
    red_sm = ''
    red_team = []
    blue_sm = ''
    blue_team = []
    for member in ctx.guild.members:
        if is_blue in member.roles:
            blue_team.append(member.name)
        if is_red in member.roles:
            red_team.append(member.name)
        if is_blue_sm in member.roles:
            blue_sm = member.name
        if is_red_sm in member.roles:
            red_sm = member.name

    # return formatting
    await ctx.send(
        "Red team ("+str(len(red_team))+") is " + str(red_team).strip('[]') +
        ". Red spymaster is " + red_sm + ".\n" +
        "Blue team ("+str(len(blue_team))+") is "+str(blue_team).strip('[]') +
        ". Blue spymaster is " + blue_sm + "."
    )


async def send_image(target, spymaster_color):
    with BytesIO() as image_bin:
        current_game.update_image_state(spymaster_color).save(image_bin, 'PNG')
        image_bin.seek(0)

        b_remain = str(len(current_game.remaining_words('Blue Spymaster')))
        r_remain = str(len(current_game.remaining_words('Red Spymaster')))
        # embed logic
        description = "```ini\n[" + b_remain + " words remain]```" + \
            "```css\n[" + r_remain + " words remain]```"
        if current_game.get_turn() == 'Red Team':
            color = discord.Colour.red()
        elif current_game.get_turn() == 'Blue Team':
            color = discord.Colour.blue()
        embed = discord.Embed(description=description, color=color)
        file = discord.File(fp=image_bin, filename='wordlist.png')
        embed.set_image(url="attachment://wordlist.png")

        # pin logic
        board_msg = await target.send(file=file, embed=embed)
        if spymaster_color is None:
            await board_msg.pin()
            to_delete = await target.channel.history().next()
            await to_delete.delete()
            if current_game.get_last_board() is not None:
                await current_game.get_last_board().unpin()
            current_game.set_last_board(board_msg)


# send words to spymaster
async def spymaster_words(ctx, team):
    is_red_sm = find(
        lambda r: r.name == 'Red Spymaster', ctx.message.guild.roles)
    is_blue_sm = find(
        lambda r: r.name == 'Blue Spymaster', ctx.message.guild.roles)
    spymaster = None

    if team == 'Red Team':
        to_check = is_red_sm
    elif team == 'Blue Team':
        to_check = is_blue_sm
    else:
        to_check = 'Error'

    for member in ctx.guild.members:
        if to_check in member.roles:
            spymaster = member
    if spymaster is not None:
        await send_image(spymaster, team)
        await spymaster.send("You are " + str(to_check) + ".")
    else:
        return


# ping current turn
async def ping_roles(ctx):
    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(ctx)
    role = None
    # check whose turn it is
    if current_game.get_clue() != '':
        if current_game.get_turn() == 'Blue Team':
            role = is_blue
        elif current_game.get_turn() == 'Red Team':
            role = is_red
        else:
            return
    elif current_game.get_clue() == '':
        if current_game.get_turn() == 'Blue Team':
            role = is_blue_sm
        elif current_game.get_turn() == 'Red Team':
            role = is_red_sm

    await ctx.send('<@&' + str(role.id) + '>')


# function to clear roles post game
async def clear_roles(ctx):
    role_list = [
        'Blue Spymaster',
        'Red Spymaster',
        'Blue Team',
        'Red Team'
    ]
    for member in ctx.guild.members:
        for role in role_list:
            await member.remove_roles(get(member.guild.roles, name=role))

bot.run(TOKEN)
