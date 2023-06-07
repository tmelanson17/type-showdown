import math
import numpy as np
# TODO: Reduce separate dependencies for tournament?
import attrs
import random

from tournament import Tournament

class Elo:
    def __init__(self, initial_elo: int=1000, K: int=32):
        self.current_elo = initial_elo
        self.K = K


def compute_expected_outcome(player_elo: Elo, opponent_elo: Elo):
    Q_player = math.pow(10, player_elo.current_elo/400)
    Q_other = math.pow(10, opponent_elo.current_elo/400)
    return (
            Q_player / (Q_player + Q_other), 
            Q_other / (Q_player + Q_other)
    )

# @param win : 1 if P1 won, 0 if P2 won, 0.5 if draw
def calculate_elo_update(win: float, elo1: Elo, elo2: Elo):
    E1, E2 = compute_expected_outcome(elo1, elo2)
    elo1_update = win - E1 
    elo2_update = 1 - win - E2
    return elo1.K*elo1_update, elo2.K*elo2_update

@attrs.define
class NTrialsElo(Tournament):
    n_trials : int = 30
    # TODO : Enforce no repeat matches
    def play_round(self, player_configs: list[np.ndarray]) -> np.ndarray:
        players = [self.player_factory(config) for config in player_configs]
        elo = [Elo() for _ in player_configs]
        indices = [i for i in range(len(players))]
        for i in range(self.n_trials):
            random.shuffle(indices)
            for i in range(0, len(indices), 2):
                p1 = players[i]
                p1_idx = indices[i]
                next_idx = (i+1)%len(indices)
                # TODO: Should I allow this? One extra iteration
                p2 = players[next_idx]
                p2_idx = indices[next_idx]
                result = self.game.play(p1, p2)
                win = 0.5 + 0.5*result
                update1, update2 = calculate_elo_update(win, elo[p1_idx], elo[p2_idx])
                elo[p1_idx].current_elo+=update1
                elo[p2_idx].current_elo+=update2
                self.game.reset()
        return np.array([e.current_elo for e in elo])

# Example (From https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/):
'''
Now let’s do an example. We’ll adopt the value K = 32. Two chess players rated r(1) = 2400 and r(2) = 2000 (so player 2 is the underdog) compete in a single match. What will be the resulting rating if player 1 wins as expected? Let’s see. Here are the transformed ratings:
Now we find out the updated Elo-rating:

r'(1) = 2400 + 32 * (1 – 0.91) = 2403
r'(2) = 2000 + 32 * (0 – 0.09) = 1997

(If Player 2 wins:)
r'(1) = 2400 + 32 * (0 – 0.91) = 2371
r'(2) = 2000 + 32 * (1 – 0.09) = 2029
'''
def test_elo():
    PA = Elo(2400, K=32)
    PB = Elo(2000, K=32)

    # Player A wins
    # Simulate 5 rounds
    win=1
    update_A, update_B = calculate_elo_update(win, PA, PB)
    print("Expected values: 2403, 1997")
    print(f"Actual value: {PA.current_elo+update_A}, {PB.current_elo+update_B}")
    update_B, update_A = calculate_elo_update(1-win, PB, PA)
    print("Expected values: 2403, 1997")
    print(f"Actual value: {PA.current_elo+update_A}, {PB.current_elo+update_B}")

    # Player B wins
    win=0
    update_A, update_B = calculate_elo_update(win, PA, PB)
    print("Expected values: 2371, 2029")
    print(f"Actual value: {PA.current_elo+update_A}, {PB.current_elo+update_B}")
    update_B, update_A = calculate_elo_update(1-win, PB, PA)
    print("Expected values: 2371, 2029")
    print(f"Actual value: {PA.current_elo+update_A}, {PB.current_elo+update_B}")
        

if __name__ == "__main__":
    test_elo()

