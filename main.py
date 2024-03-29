import random
from attrs import define, field
from enum import Enum, IntEnum
 
class Type(IntEnum):
    NULL = 0
    FIRE = 1 #9
    WATER = 2 #17
    GRASS = 3 #24
    NORMAL = 4 #30
    FLYING = 5 #35
    GROUND = 6 #39
    ELECTRIC = 7 #42
    GOD = 8 #44
    WEAK = 9
    
 
# Need to account for null
# 0=not effective, negative = not very effective times x, positive = super effective times x
EFFECTIVE_TABLE = [
 [+1, +1, +1, +1, +1, +1, +1, +1, +1, +1],# NULL 
 [+1, -2, -2, +2, +1, +1, +1, +1, +0, +2],# FIRE 
 [+1, +2, -2, -2, +1, +1, +2, +1, +0, +2],#WATER 
 [+1, -2, +2, -2, +1, -2, +2, +1, +0, +2],#GRASS 
 [+1, +1, +1, +1, +1, +1, +1, +1, +0, +2],# NRML 
 [+1, +1, +1, +2, +1, +1, +1, -2, +0, +2],#FLYNG 
 [+1, +2, +1, -2, +1, +0, +1, +2, +0, +2],# GRND 
 [+1, +1, +2, -2, +1, +2, +0, -2, +0, +2],# ELEC 
 [+1, +2, +2, +2, +2, +2, +2, +2, +1, +2],# GOD 
 [+1, +0, +0, +0, +0, +0, +0, +0, +0, +1],# WEAK 
 #NL #FR #WTR#GR #NRM#FLY#GRD#ELE#GOD#WEAK
 ]
 
# TODO: centralize damage calculations
# TODO: clean up AI state
class AI:
    def __init__(self, player):
        self._player_info = player
 
    def calculate_damage(self, pokemon, attacking_type):
        return multiply_type_effectiveness(
                AttackOption(attacking_type), 
                pokemon.types()
        )
 
    def calculate_best_move_damage(self, attacking_pokemon, recv_pokemon):
        max_damage = 0
        max_idx=0
        for i, type in enumerate(attacking_pokemon.types()):
            calc_damage = self.calculate_damage(recv_pokemon, type)
            if calc_damage > max_damage:
                max_damage = calc_damage
                max_idx = i
        return max_damage, max_idx
 
    def optimal_move(self, opposing_pokemon, options):
        # Assume you get to attack next turn, and that both moves hit
        expected_values = []
        active_pokemon = self._player_info.get_active_pokemon()
        max_opposing_damage, opposing_type = self.calculate_best_move_damage(opposing_pokemon, active_pokemon) 
        
        max_two_turn_expected_value = -99
        idx = 0
        for i, o in enumerate(options):
            if o.is_attack():
                expected_damage = 2 * (
                        self.calculate_damage(opposing_pokemon, o.type) - 
                        max_opposing_damage
                )
            elif o.is_swap():
                swap_pokemon = self._player_info.pokemon_team[o.new_idx]
                max_expected_damage = 0
                for type in swap_pokemon.types():
                    expected_damage = self.calculate_best_move_damage(swap_pokemon, opposing_pokemon)[0]
                    expected_damage -= self.calculate_damage(swap_pokemon, opposing_pokemon.types()[opposing_type])
                    expected_damage -= self.calculate_best_move_damage(opposing_pokemon, swap_pokemon)[0]
                    max_expected_damage = max(max_expected_damage, expected_damage)
            if expected_damage > max_two_turn_expected_value:
                max_two_turn_expected_value = expected_damage
                idx = i
 
        return idx
 
 
def multiply_type_effectiveness(attack, types):
    attack_type_int = int(attack.type)
    damage = attack.base_damage
    for type in types:
       if type == Type.NULL:
           continue
       type_int = int(type) 
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
 
    def types(self):
        return [self.primary_typing, self.secondary_typing]
 
 
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
    def __init__(self, player, idx):
        pokemon_team = player.pokemon_team
        self.valid = (
                pokemon_team[idx].status != Status.FNT and
                player.active_pokemon_idx != idx
        )
        self.pokemon_name = pokemon_team[idx].name
        self.new_idx = idx
 
    def __str__(self):
        return "Switch "  + self.pokemon_name
 
    def is_swap(self):
        return True
 
 
class Player:
    def __init__(self, name, pokemon_team, is_human=False):
        self.name = name
        self.pokemon_team = pokemon_team
        self.is_human = is_human
        self.active_pokemon_idx = 0
        if not is_human:
            self.ai = AI(self)
 
    def get_active_pokemon(self):
        return self.pokemon_team[self.active_pokemon_idx]
 
    def human_player_act(self, options):
        for i, o in enumerate(options):
            print(f"{i}: {o}")
        idx = input("Choose an option: ")
        return options[int(idx)]
 
    def print_current_state(self):
        pokemon = self.get_active_pokemon()
        print(pokemon.name)
        print(pokemon.primary_typing.name + "/" + pokemon.secondary_typing.name)
        print(str(pokemon.health) + "/" + str(pokemon.max_health))
 
    def act(self, state, options):
        opposing_pokemon = state
        if self.is_human:
            return self.human_player_act(options)
        else:
            return options[self.ai.optimal_move(opposing_pokemon, options)]
 
    def switch_active_pokemon(self, new_idx):
        if self.active_pokemon_idx == new_idx:
            raise Exception("Can't swap between pokemon of the same type!")
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
 
 
class Game:
 
    def __init__(self, player1, player2, debug=True):
        self._p1 = player1
        self._p2 = player2
        self._over = False
        self.debug = debug
 
    def _get_options(self, player, swap_only=False):
        options = []
        for i in range(len(player.pokemon_team)):
            option = SwapOption(player, i)
            if option.valid:
                options.append(option)
        if swap_only:
            return options
        active_pokemon = player.get_active_pokemon()
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
 
    def execute_swap(self, player, action):
        if self.debug:
            print(f"Player {player.name} swapped to {action.pokemon_name}!")
        player.switch_active_pokemon(action.new_idx)
 
    def execute_attack(self, att_player, recv_player, action):
        if self.debug:
            print(f"{att_player.get_active_pokemon().name} used {str(action)} on {recv_player.get_active_pokemon().name}!")
        
        damage = multiply_type_effectiveness(action, recv_player.get_active_pokemon().types())
        return recv_player.take_damage(damage)
 
    def play(self):
        if self._over:
            return
        # TODO: move to render
        if self.debug:
            print()
            print("======BATTTLE=======")
            print(f"======{self._p1.name}======")
            self._p1.print_current_state()
            print(f"======{self._p2.name}======")
            self._p2.print_current_state()
            print("====================")
            print()
 
        start_options_1 = self._get_options(self._p1)
        start_options_2 = self._get_options(self._p2)
 
        action1 = self._p1.act(self._p2.get_active_pokemon(), start_options_1)
        action2 = self._p2.act(self._p1.get_active_pokemon(), start_options_2)
 
 
        # flip a coin to see who goes first
        p1_first = random.random() < 0.5
        start_player = self._p1 if p1_first else self._p2
        last_player = self._p2 if p1_first else self._p1
        start_action = action1 if p1_first else action2
        last_action = action2 if p1_first else action1
            
        # Swap phase
        if start_action.is_swap():
            self.execute_swap(start_player, start_action)
        if last_action.is_swap():
            self.execute_swap(last_player, last_action)
 
        # Attack phase
        # TODO: Merge KO logic into one
        kod=False
        if start_action.is_attack():
            kod = self.execute_attack(start_player, last_player, start_action)
            if kod:
                if self.debug:
                    print(f"{last_player.get_active_pokemon().name} fainted!")
                new_options = self._get_options(last_player, swap_only=True)
                if len(new_options) > 0:
                    swp = last_player.act(start_player.get_active_pokemon(), new_options)
                    self.execute_swap(last_player, swp)
        if not kod and last_action.is_attack():
            kod = self.execute_attack(last_player, start_player, last_action)
            if kod:
                if self.debug:
                    print(f"{start_player.get_active_pokemon().name} fainted!")
                new_options = self._get_options(start_player, swap_only=True)
                if len(new_options) > 0:
                    swp = start_player.act(last_player.get_active_pokemon(), new_options)
                    self.execute_swap(start_player, swp)
 
        if self._p1.defeated():
            print("Player 2 wins!")
            self._over = True
        if self._p2.defeated():
            print("Player 1 wins!")
            self._over = True
 
    def over(self):
        return self._over
 
 
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
                        
 
 
 
def create_random_team(type_library, weights=None):
    pokemon_team = []
    types = [Type(i) for i in range(len(Type))]
    for i in range(6):
        type1, type2 = type_library.sample(weights)
        pokemon_team.append(
                Pokemon(name=f"Random{i}", primary_typing=type1, secondary_typing=type2)
        )
    return pokemon_team
 
 
def play_games(type_library, composition, n_trials=100, weights=None):
    for i in range(n_trials):
        p1 = Player("P1", create_random_team(type_library, weights), is_human=False)
        print("Player 1 team")
        print(p1.pokemon_team)
        p2 = Player("P2", create_random_team(type_library, weights), is_human=False)
        print("Player 2 team")
        print(p2.pokemon_team)
        game = Game(p1, p2, debug=False)
        i=0
        while not game._over and i < 500:
            game.play()
            i+=1
        composition.add_types(TypeLibrary.get_indices(p1.pokemon_team), not p1.defeated())
        composition.add_types(TypeLibrary.get_indices(p2.pokemon_team), not p2.defeated())
 
if __name__ == "__main__":
    types = TypeLibrary()
    composition = TeamCompositions(types.n_types)
    play_games(types, composition, n_trials=100)
    for i in range(50):
        play_games(types, composition, n_trials=10, weights=composition.win_percentages)
    win_percentages, _ = composition.breakdown_by_type()
    for i in range(len(Type)):
        print(f"{Type(i).name} : {win_percentages[i]*100}%")

