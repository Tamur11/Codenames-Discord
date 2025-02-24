from dataclasses import dataclass, field
from itertools import repeat
from random import randrange, randint, shuffle
from PIL import Image, ImageDraw, ImageFont
import copy
from data.words import default_data

from pathlib import Path
import pickle
import os

from enum import Enum

class GameState(Enum):
    UNINITIALIZED = 1
    CREATED = 2
    IN_PROGRESS = 3


@dataclass
class Team:
    color: str  # 'Red Team' or 'Blue Team'
    words: list = field(default_factory=list)  # This team's words
    guessed: list = field(default_factory=list)  # Guessed words
    clues: list = field(default_factory=list)  # Clues given
    clue_given: bool = False  # Track if a clue has been given this turn
    score: int = 0  # Team's score
    players: list = field(default_factory=list)  # Players on this team
    perm_words: list = field(default_factory=list)  # Permanent list of words


class Codenames:
    def __init__(self):
        self.word_list = default_data.copy()  # Words to choose from
        self.guessed = []  # List of guessed words
        self.guesses_remaining = 0
        self.last_board = None

        self.current_state = GameState.UNINITIALIZED

        # Select 25 random words to populate the board
        use_words = []
        self.all_words = []
        for _ in repeat(0, 25):
            chosen_word = self.word_list.pop(
                randrange(len(self.word_list)))
            use_words.append(chosen_word)
            self.all_words.append(chosen_word)

        # Both teams start with 8 cards; one team gets an extra card
        num_red = num_blue = 8
        if randint(1, 2) == 1:
            num_red += 1
            self.current_turn = 'Red Team'
        else:
            num_blue += 1
            self.current_turn = 'Blue Team'

        self.red_team = Team('Red Team')
        self.blue_team = Team('Blue Team')

        # Allocate words to teams, assassin, and bystanders
        for _ in repeat(None, num_red):
            to_add = use_words.pop()
            self.red_team.words.append(to_add)
            self.red_team.perm_words.append(to_add)

        for _ in repeat(None, num_blue):
            to_add = use_words.pop()
            self.blue_team.words.append(to_add)
            self.blue_team.perm_words.append(to_add)

        self.assassin = use_words.pop()
        self.bystander_words = use_words  # Remaining words are bystanders
        self.perm_bystander = copy.copy(use_words)

        shuffle(self.all_words)

    def get_word_list(self):
        return self.all_words

    def player_guess(self, word, team):
        # Recognize which team is guessing
        if team == 'Red Team':
            current_team = self.red_team
            other_team = self.blue_team
        else:
            current_team = self.blue_team
            other_team = self.red_team

        # Validate the guessed word
        if word not in self.all_words:
            return f"`{word}` is not in this game, try again."

        # Check if guess is the assassin
        if word == self.assassin:
            return f"{team} guessed `{word}`. Assassin! {team} lost! Use `/codenames` to start a new game."

        # Check if guess is a bystander
        if word in self.bystander_words and word not in self.guessed:
            self.guessed.append(word)
            self.bystander_words.remove(word)
            return f"{team} guessed `{word}`. That was a Bystander!"

        # Check if guess is the other team's word
        if word in other_team.words and word not in self.guessed:
            self.guessed.append(word)
            other_team.words.remove(word)
            return f"{team} guessed `{word}`. Wrong team's word!"

        # Check if the word is correct
        if word in current_team.words and word not in self.guessed:
            self.guessed.append(word)
            current_team.words.remove(word)
            return f"{team} guessed `{word}`. Correct!"

        return "Word has already been guessed."

    # Check if the game is over
    def is_game_over(self):
        if not self.blue_team.words:
            return 'Blue Team'
        if not self.red_team.words:
            return 'Red Team'
        return None

    # Update words to send to spymasters
    def remaining_words(self, team):
        if team == 'Red Spymaster':
            return self.red_team.words
        elif team == 'Blue Spymaster':
            return self.blue_team.words
        return None

    # Get current team's turn
    def get_turn(self):
        return self.current_turn

    # Swap the turn to the other team
    def swap_turn(self):
        if self.current_turn == 'Blue Team':
            self.current_turn = 'Red Team'
        elif self.current_turn == 'Red Team':
            self.current_turn = 'Blue Team'
        # Reset clue_given status when turn is swapped
        self.red_team.clue_given = False
        self.blue_team.clue_given = False

    # Get number of remaining guesses
    def get_guesses(self):
        return self.guesses_remaining

    # Set number of remaining guesses
    def set_guesses(self, guesses_remaining):
        self.guesses_remaining = guesses_remaining

    # Get the current clue
    def get_clues(self, team):
        if team == 'Red Team':
            return self.red_team.clues
        elif team == 'Blue Team':
            return self.blue_team.clues
        return []

    # Set the current clue
    def set_clue(self, clue, team):
        if team == 'Red Team':
            self.red_team.clues.append(clue)
            self.red_team.clue_given = True
        elif team == 'Blue Team':
            self.blue_team.clues.append(clue)
            self.blue_team.clue_given = True

    # Check if a clue has been given for the current turn
    def is_clue_given(self, team):
        if team == 'Red Team':
            return self.red_team.clue_given
        elif team == 'Blue Team':
            return self.blue_team.clue_given
        return False

    # Get the last board message
    def get_last_board(self):
        return self.last_board

    # Set the last board message
    def set_last_board(self, last_board):
        self.last_board = last_board

    # Check if the game has started
    def get_started(self):
        return self.state == GameState.IN_PROGRESS

    # Set the game as started
    def set_started(self):
        self.current_state = GameState.IN_PROGRESS

    def add_player(self, name, team):
        if team == 'Blue Team':
            self.blue_team.players.append(name)
        elif team == 'Red Team':
            self.red_team.players.append(name)

    def update_image_state(self, spymaster_color):
        img = Image.new('RGB', (1600, 1000))
        draw = ImageDraw.Draw(img)
        count = 0
        font = ImageFont.truetype('data/abeezee.otf', 42)

        for i in range(0, 5):
            for j in range(0, 5):
                color = None
                current_word = self.all_words[count]

                # Partial image for guessers
                if spymaster_color is None:
                    if current_word in self.guessed:
                        if current_word in self.red_team.perm_words:
                            color = (242, 96, 80)
                        elif current_word in self.blue_team.perm_words:
                            color = (82, 183, 255)
                        elif current_word in self.perm_bystander:
                            color = (209, 195, 67)
                        elif current_word == self.assassin:
                            color = (161, 158, 137)
                    else:
                        color = (255, 255, 255)

                # Full image for spymasters
                else:
                    if current_word in self.red_team.words:
                        color = (242, 185, 177)
                    elif current_word in self.blue_team.words:
                        color = (184, 225, 255)
                    elif current_word in self.bystander_words:
                        color = (209, 203, 151)
                    elif current_word == self.assassin:
                        color = (161, 158, 137)
                    # Highlight guessed words
                    if current_word in self.guessed and current_word in self.red_team.perm_words:
                        color = (242, 96, 80)
                    if current_word in self.guessed and current_word in self.blue_team.perm_words:
                        color = (82, 183, 255)
                    if current_word in self.guessed and current_word in self.perm_bystander:
                        color = (209, 195, 67)

                startX = 320 * j
                startY = 200 * i
                endX = 320 * j + 320
                endY = 200 * i + 200
                draw.rectangle(
                    [(startX, startY), (endX, endY)], color, (0, 0, 0))
                w, h = textsize(current_word, font)
                draw.text((startX + (320 - w) / 2, startY + (200 - h) / 2),
                          current_word, (0, 0, 0), font)
                count += 1
        return img

def textsize(text, font):
    im = Image.new(mode="P", size=(0, 0))
    draw_temp = ImageDraw.Draw(im)
    _, _, width, height = draw_temp.textbbox((0, 0), text=text, font=font)
    return width, height


GAME_STATE_FILENAME = "codenames.pkl"

def load_current_game() -> Codenames:
    fl = Path(GAME_STATE_FILENAME)
    if fl.exists():
        with open(fl, mode = "rb") as f:
            return pickle.load(f)
        
    return Codenames()

def save_current_game(game: Codenames):
    fl = Path(GAME_STATE_FILENAME)
    with open(fl, mode="wb") as f:
        pickle.dump(game, f)


import asyncio
import pickle

GAME_STATE_FILENAME = "game_state.pkl"

async def load_current_game() -> Codenames:
    fl = Path(GAME_STATE_FILENAME)
    if fl.exists():
        return await asyncio.to_thread(_load_pickle, fl)
    return Codenames()

async def save_current_game(game: Codenames):
    fl = Path(GAME_STATE_FILENAME)
    await asyncio.to_thread(_save_pickle, fl, game)

def _load_pickle(file_path):
    with open(file_path, mode="rb") as f:
        return pickle.load(f)

def _save_pickle(file_path, game):
    with open(file_path, mode="wb") as f:
        pickle.dump(game, f)

class GameHandler:
    def __init__(self):
        self.game = None
        self._is_game_over = False

    async def __aenter__(self):
        self.game = await load_current_game()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._is_game_over:
            os.remove(GAME_STATE_FILENAME)
        else:
            await save_current_game(self.game)

    def set_game_over(self):
        self._is_game_over = True
