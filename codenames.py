import random
from dataclasses import dataclass, field
from itertools import repeat
from random import randrange

from game import Game


@dataclass
class Team:
    color: str  # 'Red' or 'Blue'
    words: list = field(default_factory=list)  # this teams words
    guessed: list = field(default_factory=list)  # this teams guessed words
    clues: list = field(default_factory=list)  # the clues given to this team
    score: int = 0  # this teams score
    players: list = field(default_factory=list)  # the players on this team


class Codenames(Game):
    def __init__(self):
        super().__init__()
        self.word_list = open('data/words.txt').read().splitlines()  # words
        self.guessed = []  # list of words guessed
        self.guesses_remaining = 0
        self.clue = ''  # current clue

        # select 25 random words to populate board
        use_words = []  # temporary list of words being used
        self.all_words = []  # permanent list of all the words being used

        # select 25 random words to populate board
        for _ in repeat(0, 25):
            chosen_word = self.word_list.pop(randrange(len(self.word_list)))
            use_words.append(chosen_word)
            self.all_words.append(chosen_word)

        # both teams start off with 8 cards
        num_red = num_blue = 8
        # randomly select one team to start and have one extra card
        if random.randint(1, 2) == 1:
            num_red += 1
            self.current_turn = 'Red Team'
        else:
            num_blue += 1
            self.current_turn = 'Blue Team'

        self.red_team = Team('Red Team')
        self.blue_team = Team('Blue Team')

        # allocate red, blue, assassin, and bystanders
        for _ in repeat(None, num_red):
            self.red_team.words.append(use_words.pop())

        for _ in repeat(None, num_blue):
            self.blue_team.words.append(use_words.pop())

        self.assassin = use_words.pop()
        self.bystander_words = use_words  # 7 words left

    def get_word_list(self):
        return self.all_words

    def player_guess(self, word, team):
        # recognize which team is guessing and who the opposing team is
        if team == 'Red Team':
            current_team = self.red_team
            other_team = self.blue_team
        else:
            current_team = self.blue_team
            other_team = self.red_team

        # make sure word is valid
        if word not in self.all_words:
            return word + ' is not in this game, try again.'

        # check if guess is assassin
        if word in self.assassin:
            # CALL DESTRUCTOR AND DO END GAME THINGS
            return ("Assassin! " + team +
                    ' lost! Type: "!codenames" to start a new game!')

        # check if guess is bystander
        if word in self.bystander_words and word not in self.guessed:
            self.guessed.append(word)
            self.swap_turn()
            return "That was a Bystander!"

        # check if guess is wrong team
        if word in other_team.words and word not in self.guessed:
            self.guessed.append(word)
            self.swap_turn()
            return "Wrong Team's Word!"

        # check if word is correct
        if word in current_team.words and word not in self.guessed:
            self.guessed.append(word)
            return 'Correct!'

    # check if game is over
    def is_game_over(self):
        if all(elem in self.guessed for elem in self.blue_team.words):
            return 'Blue Team'
        if all(elem in self.guessed for elem in self.red_team.words):
            return 'Red Team'
        return

    # update words to send to spymasters
    def remaining_words(self, team):
        if team == 'Red Spymaster':
            return self.red_team.words
        elif team == 'Blue Spymaster':
            return self.blue_team.words
        return

    # get current team turn
    def get_turn(self):
        return self.current_turn

    # set current team turn
    def swap_turn(self):
        if self.current_turn == 'Blue Team':
            self.current_turn = 'Red Turn'
        elif self.current_turn == 'Red Team':
            self.current_turn = 'Blue Team'

    # get number of remaining guesses
    def get_guesses(self):
        return self.guesses_remaining

    # set number of remaining guesses
    def set_guesses(self, guesses_remaining):
        self.guesses_remaining = guesses_remaining

    # get clue
    def get_clue(self):
        return self.clue

    # set clue
    def set_clue(self, clue):
        self.clue = clue

    def add_player(self, name, team):
        self.players.append(name)
        if team == 'Blue Team':
            self.blue_team.players.append(name)
        elif team == 'Red Team':
            self.red_team.players.append(name)
