import os

from discord.ext import commands
from discord.utils import get, find
from dotenv import load_dotenv

from codenames import Codenames, Game

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

current_game = Game()  # variable to hold the current game being played


async def test_current_game(ctx, intended_game) -> bool:
    if current_game.__class__ == intended_game:
        return True
    else:
        await ctx.send(
            'We are not playing ' + intended_game.__name__ + ' right now.')
        return False


# create a game
@bot.command(name='codenames')
async def start(ctx):
    # THIS NEEDS TO BE REPLACED AT SOME POINT
    global current_game
    current_game = Codenames()
    await ctx.send(current_game.get_word_list())


# player guess
@bot.command(name='guess')
@commands.has_any_role('Blue Team', 'Red Team')
async def guess(ctx, word):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    user = ctx.message.author
    spymaster = None
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
        await ctx.send("Requires 2 Spymasters to begin.")
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
        response = current_game.player_guess(word.title(), team)
        if current_game.is_game_over() is not None:
            await ctx.send("Game Over! " + current_game.is_game_over() +
                           ' wins! Type: "!codenames" to start a new game!')
        await ctx.send(response)
        # catch for typos
        if 'try again' in response:
            return
        # if guess was correct
        if response == 'Correct!':
            # check if game should end
            current_game.set_guesses(int(current_game.get_guesses()) - 1)
            await ctx.send("Clue is " + current_game.get_clue() + ". " +
                           str(current_game.get_guesses()) +
                           " guesses remaining.")
            if current_game.get_guesses() < 0:
                current_game.swap_turn()
        # if guess was wrong
        else:
            if team == 'Red Team':
                await ctx.send("Now Blue Spymaster's turn.")
            elif team == 'Blue Team':
                await ctx.send("Now Red Spymaster's turn.")
    else:
        await ctx.send("Not your team's turn.")

    # update spymaster logic
    if team == 'Red Team':
        to_check = is_red_sm
        teams_spymaster = 'Red Spymaster'
    elif team == 'Blue Team':
        to_check = is_blue_sm
        teams_spymaster = 'Blue Spymaster'
    else:
        to_check = 'Error'
        teams_spymaster = 'Error'

    response = "Your remaining words: " + str(
        current_game.remaining_words(teams_spymaster))

    for member in ctx.guild.members:
        if to_check in member.roles:
            spymaster = member
    await spymaster.send(response)


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
@bot.command(name='join')
async def add_role(ctx, color, role):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    team = color.title() + " " + role.title()
    user = ctx.message.author
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
        await user.send("Your words: " +
                        str(current_game.remaining_words(team)))
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


# leave team
@bot.command(name='leave')
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
    if team == 'Blue Team' or 'Red Team':
        await user.remove_roles(get(user.guild.roles, name=team))
        await ctx.send("Left " + team + ".")
    else:
        await ctx.send("Not a valid team.")


# give clue
@bot.command(name='clue')
@commands.has_any_role('Blue Spymaster', 'Red Spymaster')
async def clue(ctx, word, number):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
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
    current_game.set_guesses(int(number) + 1)
    current_game.set_clue(word)
    await ctx.send("Clue is " + word + ". " +
                   str(current_game.get_guesses()) + " guesses remaining.")


# pass
@bot.command(name='pass')
@commands.has_any_role('Blue Team', 'Red Team')
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
        current_game.swap_turn()
        current_game.set_guesses(0)
        await ctx.send(team + " has passed their turn.")
    else:
        await ctx.send("Not your turn.")


# display which team's turn
@bot.command(name='turn')
async def turn(ctx):
    # test to see if we are currently in a Codenames game
    if not await test_current_game(ctx, Codenames):
        return

    if current_game.get_clue() != '':
        await ctx.send(current_game.get_turn() + "'s turn.")
    elif current_game.get_clue() == '':
        if current_game.get_turn() == 'Blue Team':
            await ctx.send("Blue Spymaster's turn.")
        elif current_game.get_turn() == 'Red Team':
            await ctx.send("Red Spymaster's turn.")


# command for testing
@bot.command(name='give')
async def test(ctx, word):
    if word == 'head':
        await ctx.send('Shaheen is fascist.')
    else:
        await ctx.send('Shaheen is FASCIST I SAID.')


bot.run(TOKEN)
