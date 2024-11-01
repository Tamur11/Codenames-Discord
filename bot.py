import os
import random
from io import BytesIO

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get
from dotenv import load_dotenv
from discord import AllowedMentions

from codenames import Codenames

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

allowed_mentions = AllowedMentions(roles=True, users=True)
bot = commands.Bot(command_prefix='/', intents=intents, allowed_mentions=allowed_mentions)
current_game = None  # Holds the current game instance


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


# Error handler for app commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    await interaction.response.send_message("An error occurred.", ephemeral=True)
    print(error)


# Start a new codenames game
@bot.tree.command(name='codenames', description='Start a new game of Codenames.')
async def codenames(interaction: discord.Interaction):
    global current_game
    current_game = Codenames()
    await interaction.response.send_message('Codenames game started! Add both spymasters using `/join` or `/team`, then start using `/start`.')


# Start the game
@bot.tree.command(name='start', description='Start the game.')
async def start(interaction: discord.Interaction):
    global current_game
    await interaction.response.defer()  # Defer the response

    if current_game is None:
        await interaction.followup.send("No game in progress. Use `/codenames` to start a new game.")
        return

    is_red_sm = get(interaction.guild.roles, name='Red Spymaster')
    is_blue_sm = get(interaction.guild.roles, name='Blue Spymaster')
    red_team_role = get(interaction.guild.roles, name='Red Team')
    blue_team_role = get(interaction.guild.roles, name='Blue Team')

    # Check for spymasters and team members
    no_blue_sm = no_red_sm = True
    red_team_members = []
    blue_team_members = []

    for member in interaction.guild.members:
        if is_blue_sm in member.roles:
            no_blue_sm = False
        if is_red_sm in member.roles:
            no_red_sm = False
        if blue_team_role in member.roles and is_blue_sm not in member.roles:
            blue_team_members.append(member)
        if red_team_role in member.roles and is_red_sm not in member.roles:
            red_team_members.append(member)

    # Ensure there are enough players to promote if needed
    if (no_blue_sm and len(blue_team_members) < 2) or (no_red_sm and len(red_team_members) < 2):
        await interaction.followup.send("Each team requires at least 2 players to start the game.")
        return

    # Promote a random team member to spymaster if needed
    if no_blue_sm:
        new_blue_sm = random.choice(blue_team_members)
        await new_blue_sm.add_roles(is_blue_sm)
        await new_blue_sm.remove_roles(blue_team_role)
    if no_red_sm:
        new_red_sm = random.choice(red_team_members)
        await new_red_sm.add_roles(is_red_sm)
        await new_red_sm.remove_roles(red_team_role)

    # Start game logic
    current_game.set_started(True)
    await spymaster_words(interaction, 'Blue Team')
    await spymaster_words(interaction, 'Red Team')

    await interaction.followup.send("Game started!")
    await send_image(interaction, None, await get_role_mention(interaction))


# Player guess
@bot.tree.command(name='guess', description='Guess a word.')
@app_commands.describe(word='The word you are guessing')
async def guess(interaction: discord.Interaction, word: str):
    global current_game
    if current_game is None or not current_game.get_started():
        await interaction.response.send_message("No game in progress. Use `/codenames` to start a new game.")
        return

    user = interaction.user
    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(interaction)

    # Ensure two spymasters exist
    no_blue_sm = no_red_sm = True
    for member in interaction.guild.members:
        if is_blue_sm in member.roles:
            no_blue_sm = False
        if is_red_sm in member.roles:
            no_red_sm = False
    if no_blue_sm or no_red_sm:
        await interaction.response.send_message("Unable to start game: 2 Spymasters required to play.")
        return

    # Determine guesser team
    if is_red in user.roles:
        team = 'Red Team'
    elif is_blue in user.roles:
        team = 'Blue Team'
    else:
        await interaction.response.send_message("You are not on a team.", ephemeral=True)
        return

    # Check if correct team is guessing
    if current_game.get_turn() == team and current_game.get_guesses() != 0:
        response = current_game.player_guess(word.upper(), team)
        await interaction.response.send_message(response)

        # Check if game should end
        if current_game.is_game_over() is not None:
            await interaction.followup.send(f"Game Over! {current_game.is_game_over()} wins! Use `/codenames` to start a new game.")
            await send_endgame_image(interaction)
            await clear_roles(interaction)
            await current_game.get_last_board().unpin()
            current_game = None  # Reset game
            return

        # Catch for typos
        if 'try again' in response or 'already been guessed' in response:
            return

        # If guess was correct
        if 'Correct!' in response:
            await send_image(interaction, None)
            clues = current_game.get_clues(team)
            current_clue = clues[-1]
            previous_clues = clues[:-1]
            previous_clues_text = ", ".join(f"`{clue}`" for clue in previous_clues)

            if int(current_game.get_guesses()) == -2 or int(current_game.get_guesses()) == -3:
                message = f"{await get_role_mention(interaction)} Clue is `{current_clue}`. You have infinite guesses remaining."
            else:
                current_game.set_guesses(int(current_game.get_guesses()) - 1)
                message = f"{await get_role_mention(interaction)} Clue is `{current_clue}`. You have {current_game.get_guesses()} guesses remaining."

            if previous_clues:
                message += f"\nPrevious clues: {previous_clues_text}"

            await interaction.followup.send(message)

            if current_game.get_guesses() == 0:
                current_game.set_guesses(0)
                current_game.swap_turn()
                await spymaster_words(interaction, current_game.get_turn())
                await send_image(interaction, None, await get_role_mention(interaction))

        # If guess was wrong
        elif 'Assassin' not in response:
            current_game.set_guesses(0)
            current_game.swap_turn()
            await spymaster_words(interaction, current_game.get_turn())
            await send_image(interaction, None, await get_role_mention(interaction))

        # If assassin
        else:
            await send_endgame_image(interaction)
            await clear_roles(interaction)
            await current_game.get_last_board().unpin()
            current_game = None  # Reset game
            return
    else:
        await interaction.response.send_message("Not your team's turn.")


async def color_tester(interaction):
    is_red = get(interaction.guild.roles, name='Red Team')
    is_blue = get(interaction.guild.roles, name='Blue Team')
    is_red_sm = get(interaction.guild.roles, name='Red Spymaster')
    is_blue_sm = get(interaction.guild.roles, name='Blue Spymaster')
    return is_blue, is_blue_sm, is_red, is_red_sm


# Assign roles
@bot.tree.command(name='team', description='Join a team for a specific role.')
@app_commands.describe(color='Team color', role='Spymaster or Team')
async def team(interaction: discord.Interaction, color: str, role: str):
    user = interaction.user
    team = color.title() + " " + role.title()

    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(interaction)

    # Ensure one spymaster per color
    if role.lower() == "spymaster":
        for member in interaction.guild.members:
            if color.lower() == 'blue':
                if is_blue_sm in member.roles:
                    await interaction.response.send_message("There is already a Blue Spymaster.")
                    return
            elif color.lower() == 'red':
                if is_red_sm in member.roles:
                    await interaction.response.send_message("There is already a Red Spymaster.")
                    return

    # Check if player is already on a team
    if is_red in user.roles or is_blue in user.roles:
        await interaction.response.send_message("Already on a team.")
        return

    # Check if player is spymaster
    if is_red_sm in user.roles or is_blue_sm in user.roles:
        await interaction.response.send_message("Cannot join a team as Spymaster.")
        return

    # Add spymaster role
    if team == 'Blue Spymaster' or team == 'Red Spymaster':
        await user.add_roles(get(user.guild.roles, name=team))
        await interaction.response.send_message(f"Joined {team}.")
        return

    # Add team role
    if team == 'Blue Team' or team == 'Red Team':
        if current_game:
            current_game.add_player(user.name, team)
        await user.add_roles(get(user.guild.roles, name=team))
        await interaction.response.send_message(f"Joined {team}.")
        return

    # Catch typos
    await interaction.response.send_message(f"{team} is not a valid team.")

@bot.tree.command(name='join', description='Join a team.')
async def join(interaction: discord.Interaction):
    user = interaction.user

    # Check if player is already on a team
    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(interaction)
    if is_red in user.roles or is_blue in user.roles:
        await interaction.response.send_message("Already on a team.")
        return

    # Check if player is spymaster
    if is_red_sm in user.roles or is_blue_sm in user.roles:
        await interaction.response.send_message("Already on a team.")
        return

    # Get team roles
    blue_team_role = get(interaction.guild.roles, name='Blue Team')
    red_team_role = get(interaction.guild.roles, name='Red Team')

    # Count members in each team
    blue_team_count = sum(1 for member in interaction.guild.members if blue_team_role in member.roles)
    red_team_count = sum(1 for member in interaction.guild.members if red_team_role in member.roles)

    # Determine which team to join
    if blue_team_count < red_team_count:
        chosen_team = 'Blue Team'
    elif red_team_count < blue_team_count:
        chosen_team = 'Red Team'
    else:
        chosen_team = random.choice(['Blue Team', 'Red Team'])

    # Add user to the chosen team
    await user.add_roles(get(user.guild.roles, name=chosen_team))
    if current_game:
        current_game.add_player(user.name, chosen_team)
    await interaction.response.send_message(f"Joined {chosen_team}.")

# Leave team
@bot.tree.command(name='leave', description='Leave a team.')
@app_commands.describe(color='Team color', role='Spymaster or Team')
async def leave(interaction: discord.Interaction, color: str, role: str):
    team = color.title() + " " + role.title()
    user = interaction.user
    role_obj = get(interaction.guild.roles, name=team)

    # Check if actually on team
    if role_obj not in user.roles:
        await interaction.response.send_message("You're not on that team.")
        return

    # Remove role
    if team in ['Blue Team', 'Red Team']:
        await user.remove_roles(role_obj)
        await interaction.response.send_message(f"Left {team}.")
    elif team in ['Blue Spymaster', 'Red Spymaster'] and not current_game.get_started():
        await user.remove_roles(role_obj)
        await interaction.response.send_message(f"Left {team}.")
    elif team in ['Blue Spymaster', 'Red Spymaster'] and current_game.get_started():
        await interaction.response.send_message("Cannot leave Spymaster once the game has started.")
    else:
        await interaction.response.send_message("Not a valid team.")


# Give clue
@bot.tree.command(name='clue', description='Give a clue.')
@app_commands.describe(clue='Your clue', number='Number of words')
async def clue(interaction: discord.Interaction, clue: str, number: str):
    if current_game is None or not current_game.get_started():
        await interaction.response.send_message("No game in progress.")
        return

    # Ensure only one clue is given
    if current_game.is_clue_given(current_game.get_turn()):
        await interaction.response.send_message("A clue has already been given.")
        return

    user = interaction.user
    is_red_sm = get(interaction.guild.roles, name='Red Spymaster')
    is_blue_sm = get(interaction.guild.roles, name='Blue Spymaster')

    if is_red_sm in user.roles:
        spymaster_team = 'Red Team'
    elif is_blue_sm in user.roles:
        spymaster_team = 'Blue Team'
    else:
        await interaction.response.send_message("You are not a Spymaster.", ephemeral=True)
        return

    if current_game.get_turn() != spymaster_team:
        await interaction.response.send_message("Not your team's turn.")
        return

    if str(number) == 'infinity':
        current_game.set_guesses(-3)
    elif int(number) == 0:
        current_game.set_guesses(-2)
    else:
        current_game.set_guesses(int(number) + 1)

    clue_text = f"{clue} {number}"
    current_game.set_clue(clue_text, current_game.get_turn())
    clues = current_game.get_clues(current_game.get_turn())
    current_clue = clues[-1]
    previous_clues = clues[:-1]
    previous_clues_text = ", ".join(f"`{clue}`" for clue in previous_clues)

    if current_game.get_guesses() == -2 or current_game.get_guesses() == -3:
        response = f"Clue is `{current_clue}`. You have infinite guesses remaining."
    else:
        response = f"Clue is `{current_clue}`. You have {current_game.get_guesses()} guesses remaining."

    if previous_clues:
        response += f"\nPrevious clues: {previous_clues_text}"

    await interaction.response.send_message(await get_role_mention(interaction) + " " + response)


# Pass
@bot.tree.command(name='pass', description='Pass your turn.')
async def pass_turn(interaction: discord.Interaction):
    if current_game is None or not current_game.get_started():
        await interaction.response.send_message("No game in progress.")
        return

    user = interaction.user
    is_red = get(interaction.guild.roles, name='Red Team')
    is_blue = get(interaction.guild.roles, name='Blue Team')

    # Determine player's team
    if is_red in user.roles:
        team = 'Red Team'
    elif is_blue in user.roles:
        team = 'Blue Team'
    else:
        await interaction.response.send_message("You are not on a team.", ephemeral=True)
        return

    if current_game.get_turn() == team:
        current_game.set_guesses(0)
        current_game.swap_turn()
        await spymaster_words(interaction, current_game.get_turn())
        await interaction.response.send_message(f"{team} has passed their turn.")
        await send_image(interaction, None, await get_role_mention(interaction))
    else:
        await interaction.response.send_message("Not your turn.")


# Display current turn
@bot.tree.command(name='turn', description="Display whose turn it is.")
async def turn(interaction: discord.Interaction):
    if current_game is None or not current_game.get_started():
        await interaction.response.send_message("No game in progress.")
        return

    if current_game.is_clue_given(current_game.get_turn()):
        await interaction.response.send_message(f"{current_game.get_turn()}'s turn.")
    else:
        await interaction.response.send_message(f"{current_game.get_turn()} Spymaster's turn.")


# Display team info
@bot.tree.command(name='teams', description='Display team information.')
async def teams(interaction: discord.Interaction):
    if current_game is None:
        await interaction.response.send_message("No game in progress.")
        return

    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(interaction)
    # Gather team members and spymasters
    red_sm = ''
    red_team = []
    blue_sm = ''
    blue_team = []
    for member in interaction.guild.members:
        if is_blue in member.roles:
            blue_team.append(member.name)
        if is_red in member.roles:
            red_team.append(member.name)
        if is_blue_sm in member.roles:
            blue_sm = member.name
        if is_red_sm in member.roles:
            red_sm = member.name

    # Format and send the response
    await interaction.response.send_message(
        f"Red team ({len(red_team)}): {', '.join(red_team)}\n"
        f"Red Spymaster: {red_sm}\n"
        f"Blue team ({len(blue_team)}): {', '.join(blue_team)}\n"
        f"Blue Spymaster: {blue_sm}"
    )


async def send_image(interaction, spymaster_color, role_mention=None):
    with BytesIO() as image_bin:
        current_game.update_image_state(spymaster_color).save(image_bin, 'PNG')
        image_bin.seek(0)

        b_remain = str(len(current_game.remaining_words('Blue Spymaster')))
        r_remain = str(len(current_game.remaining_words('Red Spymaster')))
        # Embed logic
        description = f"```ansi\n\u001b[34m[Blue - {b_remain} words remain]\u001b[0m```" + f"```ansi\n\u001b[31m[Red - {r_remain} words remain]\u001b[0m```"
        color = discord.Colour.red() if current_game.get_turn() == 'Red Team' else discord.Colour.blue()
        embed = discord.Embed(description=description, color=color)
        file = discord.File(fp=image_bin, filename='wordlist.png')
        embed.set_image(url="attachment://wordlist.png")

        # Pin logic
        board_msg = await interaction.channel.send(content=role_mention, file=file, embed=embed)
        if spymaster_color is None:
            await board_msg.pin()
            if current_game.get_last_board() is not None:
                await current_game.get_last_board().unpin()
            current_game.set_last_board(board_msg)


# Send words to spymaster
async def spymaster_words(interaction, team):
    is_red_sm = get(interaction.guild.roles, name='Red Spymaster')
    is_blue_sm = get(interaction.guild.roles, name='Blue Spymaster')
    spymaster = None

    if team == 'Red Team':
        to_check = is_red_sm
    elif team == 'Blue Team':
        to_check = is_blue_sm
    else:
        to_check = None

    for member in interaction.guild.members:
        if to_check in member.roles:
            spymaster = member
    if spymaster is not None:
        # Send image to spymaster
        await send_image_to_spymaster(spymaster, team)
        await spymaster.send(f"You are {to_check.name}.")
    else:
        return


async def send_image_to_spymaster(spymaster, team):
    with BytesIO() as image_bin:
        current_game.update_image_state(team).save(image_bin, 'PNG')
        image_bin.seek(0)
        file = discord.File(fp=image_bin, filename='wordlist.png')
        await spymaster.send(file=file)


async def send_endgame_image(interaction):
    with BytesIO() as image_bin:
        current_game.update_image_state(True).save(image_bin, 'PNG')
        image_bin.seek(0)
        file = discord.File(fp=image_bin, filename='wordlist.png')
        await interaction.followup.send(file=file)


async def get_role_mention(interaction):
    is_blue, is_blue_sm, is_red, is_red_sm = await color_tester(interaction)
    role = None
    # Determine whose turn it is
    if current_game.is_clue_given(current_game.get_turn()):
        role = is_blue if current_game.get_turn() == 'Blue Team' else is_red
    else:
        role = is_blue_sm if current_game.get_turn() == 'Blue Team' else is_red_sm

    return role.mention


# Clear roles after game ends
async def clear_roles(interaction):
    role_list = [
        'Blue Spymaster',
        'Red Spymaster',
        'Blue Team',
        'Red Team'
    ]
    for member in interaction.guild.members:
        for role_name in role_list:
            role_obj = get(member.guild.roles, name=role_name)
            if role_obj in member.roles:
                await member.remove_roles(role_obj)


bot.run(TOKEN)