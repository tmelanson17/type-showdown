from pokemon import TypeLibrary, PokemonGame, play_pokemon_tournament, print_teams
from genetic_algorithm import GeneticAlgorithm 

if __name__ == "__main__":
    types = TypeLibrary()
    game = PokemonGame(n_iterations=500, debug=False)
    fn = lambda configs : play_pokemon_tournament(game, types, configs)
    represent_fn = lambda config : print_teams(types, config)
    g = GeneticAlgorithm(
            population_size=100, 
            max_iterations=3,
            min_iterations=2,
            n_convergence_iterations=2,
            n_gene_variants=types.n_types, 
            n_parents=40,
            n_mutations=15,
            chromosone_length=6, 
            fitness_fn=fn,
            represent_fn=represent_fn)

    g.train()
