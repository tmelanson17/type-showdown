import random
from attrs import define, field
from enum import Enum, IntEnum
import numpy as np
from tournament import Player, Game, Tournament
from type_matchup_reader import Type, EFFECTIVE_TABLE


# TODO: centralize damage calculations
# TODO: clean up AI state
class AI:
    def __init__(self, config):
        pass
 
    def calculate_damage(self, pokemon, attacking_type):
        return multiply_type_effectiveness(
                attacking_type, 
                pokemon.types
        )
 
    def calculate_best_move_damage(self, attacking_pokemon, recv_pokemon):
        max_damage = 0
        max_idx=0
        i=0
        for typ in attacking_pokemon.types:
            calc_damage = self.calculate_damage(recv_pokemon, typ)
            if calc_damage > max_damage:
                max_damage = calc_damage
                max_idx = i
            i+=1
        return max_damage, max_idx
 
    def optimal_move(self, state, options):
        opposing_pokemon  = state['opposing_pokemon']
        active_pokemon = state['active_pokemon']
        pokemon_team = state['pokemon_team']
        # Assume you get to attack next turn, and that both moves hit
        max_opposing_damage, opposing_type = self.calculate_best_move_damage(opposing_pokemon, active_pokemon) 
        
        max_two_turn_expected_value = -99
        idx = 0
        for i, o in enumerate(options):
            if o.is_attack():
                expected_damage = 2 * (
                        self.calculate_damage(opposing_pokemon, o.type) - 
                        max_opposing_damage
                )
            else:
                swap_pokemon = pokemon_team[o.new_idx]
                expected_damage = self.calculate_best_move_damage(swap_pokemon, opposing_pokemon)[0]
                expected_damage -= self.calculate_damage(swap_pokemon, opposing_pokemon.types[opposing_type])
                expected_damage -= self.calculate_best_move_damage(opposing_pokemon, swap_pokemon)[0]
            if expected_damage > max_two_turn_expected_value:
                max_two_turn_expected_value = expected_damage
                idx = i
 
        return idx
        
        
 
def multiply_type_effectiveness(attack_type, types):
    attack_type_int = int(attack_type)
    # TODO: not use base damage somehow
    damage = 4
    for typ in types:
       type_int = int(typ) 
       effectiveness = EFFECTIVE_TABLE[attack_type_int][type_int]
       if effectiveness < 0:
           damage = damage // abs(effectiveness)
       else:
           damage *= effectiveness
    return damage
 
 
# Ignoring most statuses for now except NRM, FNT
class Status(Enum):
    NRM = 0
    PAR = 1
    SLP = 2
    BRN = 3
    FRZ = 4
    FNT = 5
 
# TODO : Check that first type isn't null
# TODO: Set health to max health
@define
class Pokemon(object):
    name : str
    primary_typing : Type
    secondary_typing : Type = field(default=Type.NULL)
    health : int = field(default=16)
    max_health: int = field(default=16)
    status : Status = field(default=Status.NRM)
    types : list = field(init=False)
 
    @types.default
    def _get_types(self):
        return [self.primary_typing, self.secondary_typing]

@define
class PokemonTeam(object):
    pokemon_team : list[Pokemon]
    active_pokemon_idx : int = field(default=0)
 
    def get_active_pokemon(self):
        return self.pokemon_team[self.active_pokemon_idx]
 
    def switch_active_pokemon(self, new_idx):
        if self.active_pokemon_idx == new_idx:
            raise Exception("Can't swap to the same pokemon!")
        self.active_pokemon_idx = new_idx
 
    # Returns true if kod, false if not
    def take_damage(self, dmg):
        pokemon = self.get_active_pokemon()
        pokemon.health = max(pokemon.health - dmg, 0)
        if pokemon.health == 0:
            pokemon.status = Status.FNT
            return True
        return False
 
    def defeated(self):
        for pokemon in self.pokemon_team:
            if not pokemon.status == Status.FNT:
                return False
        return True

    def print_current_state(self):
        pokemon = self.get_active_pokemon()
        print(pokemon.name)
        print(pokemon.primary_typing.name + "/" + pokemon.secondary_typing.name)
        print(str(pokemon.health) + "/" + str(pokemon.max_health))
 

    def __len__(self):
        return len(self.pokemon_team)


    def __getitem__(self, i):
        return self.pokemon_team[i]

 
 
class Option():
    def is_attack(self):
        return False
 
    def is_swap(self):
        return False
 
class AttackOption(Option):
    def __init__(self, type):
        self.type = type
        self.valid = self.type != Type.NULL
        self.base_damage = 4
 
    def __str__(self):
        return self.type.name + " Attack"
 
    def is_attack(self):
        return True
 
 
class SwapOption(Option):
    def __init__(self, pokemon_team, idx):
        self.valid = (
                pokemon_team[idx].status != Status.FNT and
                pokemon_team.active_pokemon_idx != idx
        )
        self.pokemon_name = pokemon_team[idx].name
        self.new_idx = idx
 
    def __str__(self):
        return "Switch "  + self.pokemon_name
 
    def is_swap(self):
        return True
 
@define
class PokemonState:
    opposing_pokemon: Pokemon
    active_pokemon: Pokemon
    team: PokemonTeam

 
class Player:
    def __init__(self, name, pokemon_config, is_human=False):
        self.name = name
        self.pokemon_config = pokemon_config
        self.is_human = is_human
        self.active_pokemon_idx = 0
        if not is_human:
            self.ai = AI(pokemon_config)
 
    def human_player_act(self, options):
        for i, o in enumerate(options):
            print(f"{i}: {o}")
        idx = input("Choose an option: ")
        return options[int(idx)]
 

    def act(self, state, options):

        if self.is_human:
            return self.human_player_act(options)
        else:
            return options[self.ai.optimal_move(state, options)]
 
 
'''
    Notes:
    Should the teams be extracted from player?
'''
class PokemonGame(Game):
 
    def __init__(self, n_iterations, debug=True):
        self._over = False
        self._n_iterations = n_iterations
        self._iterations = 0
        self.debug = debug

    def reset(self):
        self._over = False
        self._iterations = 0
 
    def _get_options(self, pokemon_team, swap_only=False):
        options = []
        for i in range(len(pokemon_team)):
            option = SwapOption(pokemon_team, i)
            if option.valid:
                options.append(option)
        if swap_only:
            return options
        active_pokemon = pokemon_team.get_active_pokemon()
        # This should only be triggered if game is over.
        if active_pokemon.status == Status.FNT:
            return options
        primary_attack = AttackOption(active_pokemon.primary_typing)
        if not primary_attack.valid:
            raise Exception("Pokemon needs to have a type!")
        options.append(primary_attack)
        secondary_attack = AttackOption(active_pokemon.secondary_typing)
        if secondary_attack.valid:
            options.append(secondary_attack)
        return options
 
    def execute_swap(self, player, team, action):
        if self.debug:
            print(f"Player {player.name} swapped to {action.pokemon_name}!")
        team.switch_active_pokemon(action.new_idx)
 
    def execute_attack(self, att_team, recv_team, action):
        if self.debug:
            print(f"{att_team.get_active_pokemon().name} used {str(action)} on {recv_team.get_active_pokemon().name}!")
        
        damage = multiply_type_effectiveness(action.type, recv_team.get_active_pokemon().types)
        return recv_team.take_damage(damage)
 
    def play_round(self, player1, player2, p1_team, p2_team):
        if self._over:
            return
        # TODO: move to render
        if self.debug:
            print()
            print("======BATTTLE=======")
            print(f"======{player1.name}======")
            p1_team.print_current_state()
            print(f"======{player2.name}======")
            p2_team.print_current_state()
            print("====================")
            print()
 
        start_options_1 = self._get_options(p1_team)
        start_options_2 = self._get_options(p2_team)

        state1 = {
                'opposing_pokemon': p2_team.get_active_pokemon(), 
                'active_pokemon': p1_team.get_active_pokemon(), 
                'pokemon_team': p1_team
        }
        state2 = {
                'opposing_pokemon': p1_team.get_active_pokemon(), 
                'active_pokemon': p2_team.get_active_pokemon(), 
                'pokemon_team': p2_team
        }
 
        action1 = player1.act(state1, start_options_1)
        action2 = player2.act(state2, start_options_2)
 
 
        # flip a coin to see who goes first
        p1_first = random.random() < 0.5
        start_team = p1_team if p1_first else p2_team
        start_player = player1 if p1_first else player2
        start_state = state1 if p1_first else state2
        start_action = action1 if p1_first else action2
        last_team = p2_team if p1_first else p1_team
        last_player = player2 if p1_first else player1
        last_state = state2 if p1_first else state1
        last_action = action2 if p1_first else action1
            
        # Swap phase
        if start_action.is_swap():
            self.execute_swap(start_player, start_team, start_action)
        if last_action.is_swap():
            self.execute_swap(last_player, last_team, last_action)
 
        # Attack phase
        # TODO: Merge KO logic into one
        kod=False
        if start_action.is_attack():
            kod = self.execute_attack(start_team, last_team, start_action)
            if kod:
                if self.debug:
                    print(f"{last_team.get_active_pokemon().name} fainted!")
                new_options = self._get_options(last_team, swap_only=True)
                if len(new_options) > 0:
                    swp = last_player.act(last_state, new_options)
                    self.execute_swap(last_player, last_team, swp)
        if not kod and last_action.is_attack():
            kod = self.execute_attack(last_team, start_team, last_action)
            if kod:
                if self.debug:
                    print(f"{start_team.get_active_pokemon().name} fainted!")
                new_options = self._get_options(start_team, swap_only=True)
                if len(new_options) > 0:
                    swp = start_player.act(start_state, new_options)
                    self.execute_swap(start_player, start_team, swp)
 
        if p1_team.defeated():
            #print("Player 2 wins!")
            self._over = True
        if p2_team.defeated():
            #print("Player 1 wins!")
            self._over = True   
        self._iterations += 1
 
    def over(self):
        return self._over or self._iterations >= self._n_iterations
 
    def play(self, player1, player2):
        p1_team = generate_team(player1.pokemon_config)
        p2_team = generate_team(player2.pokemon_config)
        while not self.over():
            self.play_round(player1, player2, p1_team, p2_team)
        result=0
        if p2_team.defeated():
            result=1
        elif p1_team.defeated():
            result=-1
        return result

class TypeLibrary:
    def __init__(self):
        self._types = self._create_types()
 
    def _create_types(self):
        type_combos = []
        n_types = len(Type)
        for i in range(n_types):
            for j in range(i+1, n_types):
                # Set i to be type2 since that can include Type.NULL
                type1 = Type(j)
                type2 = Type(i)
                type_combos.append((type1, type2))
        return type_combos
 
    def sample(self, weights=None):
        return random.choices(self._types, weights)[0]
 
    @staticmethod
    def get_index(type1, type2):
        i1 = int(type1)
        i2 = int(type2)
        return i1 - i2 - 1 + i2*len(Type) - (i2 * (i2+1))//2
 
    @staticmethod
    def get_indices(pokemon_team):
        return [
            TypeLibrary.get_index(pokemon.primary_typing, pokemon.secondary_typing)
            for pokemon in pokemon_team
        ]
 
    @property
    def n_types(self):
        return len(self._types)

    def get_types(self, idx):
        return self._types[int(idx)]
 
 
class TeamCompositions:
    def __init__(self, n_combos):
        self.total_counts = [0 for i in range(n_combos)]
        self.win_percentages = [0 for i in range(n_combos)]
 
    def calculate_win_percentage(self, win_percentage, prev_total, n_win, n_total):
        return (win_percentage * prev_total + n_win) / (prev_total + n_total)
 
    def add_types(self, idxs, won):
        print(idxs)
        for idx in idxs:
            self.win_percentages[idx] = self.calculate_win_percentage(
                    self.win_percentages[idx],
                    self.total_counts[idx],
                    int(won),
                    1
            )
            self.total_counts[idx] += 1
 
    def breakdown_by_type(self):
        n_types = len(Type)
        percentage_by_type = [0 for i in range(n_types)]
        total_counts_by_type = [0 for i in range(n_types)]
        for i in range(n_types):
            for j in range(i+1, n_types):
                idx = TypeLibrary.get_index(j, i)
                for type_i in [i, j]:
                    percentage_by_type[type_i] = self.calculate_win_percentage(
                            percentage_by_type[type_i],
                            total_counts_by_type[type_i],
                            self.win_percentages[idx]*self.total_counts[idx],
                            self.total_counts[idx]
                    )
                
        return percentage_by_type, total_counts_by_type
                        
 
 
 
def create_random_configs(n_types, n_players, n_pokemon=6):
    return [
            [np.random.randint(n_types) for i in range(n_pokemon)]
            for j in range(n_players)
    ]


def generate_team(config):
    return PokemonTeam([
            Pokemon(name=f"Random{i}", primary_typing=type1, secondary_typing=type2)
            for i, (type1, type2) in enumerate(config)
    ])

def generate_player(config):
    return Player("Youngster Joey", config, is_human=False)

def print_teams(type_library, configs):
    type_configs = convert_configs(type_library, configs)
    print("==========")
    for cfg in type_configs:
        team_string = "Team: ["
        for type1, type2 in cfg:
            team_string += f"|{type1.name}, {type2.name}| "
        team_string += "]\n"
        print(team_string)
    print("==========")

def convert_configs(type_library, input_configs):
    print(input_configs)
    return [
            [type_library.get_types(idx) for idx in config]
            for config in input_configs
    ]

# TODO: fix this so the tournament/fitness function can be run independently of type
def play_pokemon_tournament(game, type_library, input_configs):
    factory = generate_player
    tournament = Tournament(game, factory)
    configs = convert_configs(type_library, input_configs)
    wins = tournament.play_round(configs)
    print(wins)
    return wins


if __name__ == "__main__":
    # Test TypeLibrary derives

    types = TypeLibrary()
    # print(f"Types: {types.n_types}")
    # print("Expected: |Fire/Null|, |God/Null|, |Weak/God|, |Weak/Flying|, |Flying/Grass|, |Ground/Normal|")
    # print_teams(types, [[0,8,44,38,25,31]])
    composition = TeamCompositions(types.n_types)
    configs = create_random_configs(n_types=types.n_types, n_players=50)
    game = PokemonGame(n_iterations=500, debug=False)
    results = play_pokemon_tournament(game, types, configs)
    print(results)
