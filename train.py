from pokemon import TypeLibrary, PokemonGame, play_pokemon_tournament, print_teams
from genetic_algorithm import GeneticAlgorithm 

if __name__ == "__main__":
    types = TypeLibrary()
    game = PokemonGame(n_iterations=500, debug=False)
    fn = lambda configs : play_pokemon_tournament(game, types, configs)
    represent_fn = lambda config : print_teams(types, config)
    population_size=128
    g = GeneticAlgorithm(
            population_size=population_size, 
            max_iterations=1000,
            min_iterations=2,
            n_convergence_iterations=2,
            n_gene_variants=types.n_types, 
            n_parents=population_size//2,
            n_mutations=(3*population_size)//4,
            chromosone_length=6, 
            fitness_fn=fn,
            represent_fn=represent_fn)

    g.train()
