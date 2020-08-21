import random

from itertools import repeat
from random import randrange

game_state = {
    'all': [],
    'current_turn': '',
    'Red Team': [],
    'Blue Team': [],
    'bystander': [],
    'assassin': [],
    'guessed': [],
    'clue': '',
    'guesses_remaining': 0
}


def create_game():
    word_list = open('data/words.txt').read().splitlines()
    use_words = []
    all_words = []

    # select 25 random words to populate board
    for i in repeat(0, 25):
        chosen_word = word_list.pop(randrange(len(word_list)))
        use_words.append(chosen_word)
        all_words.append(chosen_word)

    current_turn = 'Blue Team'
    # determine who starts
    if random.randint(1, 2) == 1:
        num_red = 9
        num_blue = 8
        current_turn = 'Red Team'
    else:
        num_red = 8
        num_blue = 9

    red_words = []
    blue_words = []
    bystander_words = []

    # allocate red, blue, bystander, assassin
    for i in repeat(0, num_red):
        chosen_word = use_words.pop(randrange(len(use_words)))
        red_words.append(chosen_word)

    for i in repeat(0, num_blue):
        chosen_word = use_words.pop(randrange(len(use_words)))
        blue_words.append(chosen_word)

    for i in repeat(0, 7):
        chosen_word = use_words.pop(randrange(len(use_words)))
        bystander_words.append(chosen_word)

    # fill game_state
    global game_state
    game_state = {
        'all': all_words,
        'current_turn': current_turn,
        'Red Team': red_words,
        'Blue Team': blue_words,
        'bystander': bystander_words,
        'assassin': use_words,
        'guessed': [],
        'clue': '',
        'guesses_remaining': 0
    }

    return(all_words)


def player_guess(word, team):
    global game_state
    team_words = game_state[team]
    if team == 'Blue Team':
        not_words = game_state['Red Team']
    else:
        not_words = game_state['Blue Team']

    # make sure word is valid
    if word not in game_state['all']:
        return(word + ' is not in this game, try again.')

    # check if guess is assassin
    if word in game_state['assassin']:
        game_state = {
            'all': [],
            'current_turn': '',
            'Red Team': [],
            'Blue Team': [],
            'bystander': [],
            'assassin': [],
            'guessed': [],
            'clue': '',
            'guesses_remaining': 0
        }
        return("Assassin! " + team +
               ' lost! Type: "!codenames" to start a new game!')

    # check if guess is bystander
    if word in game_state['bystander'] and word not in game_state['guessed']:
        game_state['guessed'].append(word)
        swap_turn(get_turn())
        return("That was a Bystander!")

    # check if guess is wrong team
    if word in not_words and word not in game_state['guessed']:
        game_state['guessed'].append(word)
        swap_turn(get_turn())
        return("Wrong Team's Word!")

    # check if word is correct
    if word in team_words and word not in game_state['guessed']:
        game_state['guessed'].append(word)
        return('Correct!')


# check if game is over
def is_game_over():
    if all(elem in game_state['guessed'] for elem in game_state['Blue Team']):
        return 'Blue Team'
    if all(elem in game_state['guessed'] for elem in game_state['Red Team']):
        return 'Red Team'
    return


# update words to send to spymasters
def update_spymaster(team):
    if team == 'Red Spymaster':
        team = 'Red Team'
    elif team == 'Blue Spymaster':
        team = 'Blue Team'
    return game_state[team]


# get current team turn
def get_turn():
    return game_state['current_turn']


# set current team turn
def swap_turn(current_turn):
    if current_turn == 'Blue Team':
        game_state['current_turn'] = 'Red Turn'
    elif current_turn == 'Red Team':
        game_state['current_turn'] = 'Blue Team'


# get number of remaining guesses
def get_guesses():
    return game_state['guesses_remaining']


# set number of remaining guesses
def set_guesses(guesses_remaining):
    game_state['guesses_remaining'] = guesses_remaining


# get clue
def get_clue():
    return game_state['clue']


# set clue
def set_clue(clue):
    game_state['clue'] = clue
