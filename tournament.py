import attrs
from typing import Callable, Any
from abc import ABC, abstractmethod
from enum import Enum
import numpy as np

class Player(ABC):
    @abstractmethod
    def act(self, options: list[Enum], state: dict):
        pass


# Abstract function
class Game(ABC):
    # 1 if p1 won, -1 if p2 won, 0 if draw
    @abstractmethod
    def play(self, player1: Player, player2: Player):
        pass

    @abstractmethod
    def reset(self):
        pass


@attrs.define
class Tournament:
    game : Game
    # FIXIT: Get the function typing down
    player_factory : Any # Callable[list[Integer

    def play_round(self, player_configs: list[np.ndarray]) -> np.ndarray:
        players = [self.player_factory(config) for config in player_configs]
        wins = np.zeros(len(player_configs))
        for i, p1 in enumerate(players):
            for j, p2 in enumerate(players[(i+1):]):
                result = self.game.play(p1, p2)
                # TODO: Make result an enum
                if result >= 0: 
                    wins[i] += 1
                if result <= 0:
                    wins[j+i+1] += 1
                self.game.reset()
        return wins

# Test classes
class RockPaperScissorsOptions(Enum):
    ROCK=0
    PAPER=1
    SCISSORS=2

class RandomRPSPlayer(Player):
    def __init__(self, config):
        self.probs = config / config.sum()

    def act(self, options, metadata):
        i = np.random.choice(options, p=self.probs)
        return RockPaperScissorsOptions(i)

class RPS(Game):
    def __init__(self):
        self._p1_options = list(RockPaperScissorsOptions)
        self._p2_options = list(RockPaperScissorsOptions)

    def play(self, player1: Player, player2: Player):
        p1_option = player1.act(self._p1_options, {})
        p2_option = player2.act(self._p2_options, {})
        print(p1_option)
        print(p2_option)
        if p1_option.value == ((p2_option.value + 1) % 3):
            return 1
        elif p2_option.value == ((p1_option.value + 1) % 3):
            return -1
        else:
            return 0
        

if __name__ == "__main__":
    game = RPS()
    p1 = RandomRPSPlayer(np.array([1,0,0]))
    p2 = RandomRPSPlayer(np.array([0,1,0]))
    p3 = RandomRPSPlayer(np.array([0,0,1]))
    print("Game 1: Rock vs. Paper (expect -1)")
    print(game.play(p1, p2))
    print("Game 2: Paper vs. Rock (expect 1)")
    print(game.play(p2, p1))
    print("Game 3: Rock vs. Rock (expect 0)")
    print(game.play(p1, p1))
    print("Game 4: Rock vs. Scissors (expect 1)")
    print(game.play(p1, p3))

    # Now test the tournament
    player_factory = lambda config: RandomRPSPlayer(config)
    tournament = Tournament(game, player_factory)
    winner = np.array([0,1,0])
    loser1 = np.array([1,0,0])
    loser2 = np.array([1,0,0])
    results = tournament.play_round([winner, loser1, loser2])
    print(results)


    # Equal
    p1 = np.array([0,1,0])
    p2 = np.array([1,0,0])
    p3 = np.array([0,0,1])
    results = tournament.play_round([p1, p2, p3])
    print(results)
