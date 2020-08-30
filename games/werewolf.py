from games.game import Game
from dataclasses import dataclass
from random import shuffle


@dataclass
class Player:
    name: str  # player name
    role: str  # player role


class Werewolf(Game):
    def __init__(self):
        super().__init__()
        self.role_list = []
        self.players = []

    def add_role(self, role):
        self.role_list.append(role)

    def add_players(self, name):
        self.players.append(name)

    def get_role_list(self):
        return self.role_list

    def get_players(self):
        return self.players

    def assign_roles(self):
        shuffle(self.role_list)
        roles = self.role_list
        self.players[:] = [Player(x, roles.pop()) if x is not None
                           else x for x in self.players]
