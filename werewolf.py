from game import Game
from dataclasses import dataclass


@dataclass
class Player:
    role: list = str  # player role


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
