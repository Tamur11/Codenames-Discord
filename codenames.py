import random
from dataclasses import dataclass, field
from itertools import repeat
from random import randrange, shuffle

from PIL import Image, ImageDraw, ImageFont

from game import Game


@dataclass
class Team:
    color: str  # 'Red' or 'Blue'
    words: list = field(default_factory=list)  # this teams words
    guessed: list = field(default_factory=list)  # this teams guessed words
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
            self.red_team.words.append(
                use_words.pop(randrange(len(use_words))))

        for _ in repeat(None, num_blue):
            self.blue_team.words.append(
                use_words.pop(randrange(len(use_words))))

        self.assassin = use_words.pop(randrange(len(use_words)))
        self.bystander_words = use_words  # 7 words left

        shuffle(self.all_words)

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
            other_team.words.remove(word)
            self.swap_turn()
            return "Wrong Team's Word!"

        # check if word is correct
        if word in current_team.words and word not in self.guessed:
            self.guessed.append(word)
            current_team.words.remove(word)
            return 'Correct!'

    # check if game is over
    def is_game_over(self):
        if not self.blue_team.words:
            return 'Blue Team'
        if not self.red_team.words:
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
            self.current_turn = 'Red Team'
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

    def update_image_state(self, spymaster_color):
        img = Image.new('RGB', (1600, 1000))
        draw = ImageDraw.Draw(img)
        count = 0
        font = ImageFont.truetype('data/abeezee.otf', 48)

        for i in range(0, 5):
            for j in range(0, 5):
                color = None
                current_word = self.all_words[count]

                # partial image for guessers
                if spymaster_color is None:
                    if current_word in self.guessed:
                        if current_word in self.red_team.words:
                            color = (242, 96, 80)
                        elif current_word in self.blue_team.words:
                            color = (133, 204, 255)
                        elif current_word in self.bystander_words:
                            color = (209, 195, 67)
                        elif current_word in self.assassin:
                            color = (161, 158, 137)
                    else:
                        color = (255, 255, 255)

                # full image for spymasters
                else:
                    if current_word in self.red_team.words:
                        color = (242, 96, 80)
                    elif current_word in self.blue_team.words:
                        color = (133, 204, 255)
                    elif current_word in self.bystander_words:
                        color = (209, 195, 67)
                    elif current_word in self.assassin:
                        color = (161, 158, 137)
                    # highlight guessed words green
                    if current_word in self.guessed:
                        color = (134, 249, 107)

                startX = 320 * j
                startY = 200 * i
                endX = 320 * j + 320
                endY = 200 * i + 200
                draw.rectangle(
                    [(startX, startY), (endX, endY)], color, (0, 0, 0))
                w, h = draw.textsize(current_word, font)
                draw.text((startX + (320 - w) / 2, startY + (200 - h) / 2),
                          current_word, (0, 0, 0), font)
                count += 1
        return img
