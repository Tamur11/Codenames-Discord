import random
from itertools import repeat
from random import randrange
from dataclasses import dataclass


@dataclass
class Team:
    color: str  # 'Red' or 'Blue'
    words = []  # this teams words
    guessed = []  # the words this team has guessed
    clues = []  # the clues given to this team
    score = 0  # this teams score


class Codenames:
    def __init__(self):
        # list of all known words
        self.word_list = open('data/words.txt').read().splitlines()
        self.guessed = []  # list of words guessed by either team in this game
        self.guesses_remaining = 0  # not sure what this is for but I'll leave it

        # select 25 random words to populate board
        use_words = []  # temporary list of words being used in this game
        self.all_words = []  # permanent list of all the words being used in this game

        # randomly select 25 words to be used for this game
        for _ in repeat(None, 25):
            # pop a random word out of our word list
            chosen_word = self.word_list.pop(randrange(len(self.word_list)))
            # store the word in both use_words and all_words
            use_words.append(chosen_word)
            self.all_words.append(chosen_word)

        # both teams start off with 8 cards
        num_red = num_blue = 8
        # randomly select one team to start and have one extra card
        if random.randint(1, 2) == 1:
            num_red += 1
            self.current_turn = 'Red'
        else:
            num_blue += 1
            self.current_turn = 'Blue'

        self.red_team = Team('Red')
        self.blue_team = Team('Blue')

        # allocate red, blue, assassin, and bystanders
        for _ in repeat(None, num_red):
            self.red_team.words.append(use_words.pop())

        for _ in repeat(None, num_blue):
            self.blue_team.guessed.append(use_words.pop())

        self.assassin = use_words.pop()
        self.bystander_words = use_words  # 7 words left

    # check if game is over
    def is_game_over(self):
        if all(elem in self.guessed for elem in self.blue_team.words):
            return 'Blue Team'
        if all(elem in self.guessed for elem in self.blue_team.words):
            return 'Red Team'
        return

    def get_word_list(self):
        return self.all_words

    def player_guess(self, word, team):
        # recognize which team is guessing and who the opposing team is
        if team == 'Red':
            current_team = self.red_team
            other_team = self.blue_team
        else:
            current_team = self.blue_team
            other_team = self.red_team

        # make sure word is valid
        if word not in self.all_words:
            return 'word not in this game'

        # update the guessed lists
        current_team.guessed.append(word)
        self.guessed.append(word)

        # check if guess is assassin
        if word in self.assassin:
            return 'assassin!'

        # check if guess is bystander
        if word in self.bystander_words and word not in self.guessed:
            return 'bystander!'

        # check if guess is wrong team
        if word in other_team.words and word not in self.guessed:
            other_team.score += 1
            return 'other teams word!'

        # check if word is correct
        if word in current_team.words and word not in self.guessed:
            current_team.score += 1
            return 'correct!'

    # update words to send to spymasters
    def update_spymaster(self, team):
        if team == 'Red':
            return self.red_team
        elif team == 'Blue':
            return self.blue_team

    # get current team turn
    def get_turn(self):
        return self.current_turn

    # set current team turn
    def swap_turn(self):
        if self.current_turn == 'Blue Team':
            self.current_turn = 'Red Turn'
        elif self.current_turn == 'Red Team':
            self.current_turn = 'Blue Team'

    # set current team turn
    def set_turn(self, c_turn):
        self.current_turn = c_turn

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
