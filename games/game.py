from abc import ABC, abstractmethod


class Game(ABC):
    def __init__(self):
        self.players = []
