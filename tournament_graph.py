import attrs
import random

class TournamentGraph:
    def __init__(self, n_nodes, n_challenges=10):
        self.nodes = [[] for node in range(n_nodes)]
        self._n_challenges = n_challenges
        self.create_graph()

    def create_graph(self):
        n_nodes = len(self.nodes)
        for i_node, node in enumerate(self.nodes):
            if i_node == len(self.nodes)-1:
                break
            nodes_to_attach = self._n_challenges - len(node)
            i=0
            while i < nodes_to_attach:
                potential_node_idx = random.randrange(i_node+1, n_nodes)
                potential_node = self.nodes[potential_node_idx]
                print(potential_node)
                if len(potential_node) < self._n_challenges and i_node not in potential_node:
                    i+=1
                    self.nodes[potential_node_idx].append(i_node)
                    self.nodes[i_node].append(potential_node_idx)

if __name__ == "__main__":
    # Create fully connected 10-node graph
    graph = TournamentGraph(n_nodes=20, n_challenges=2)
    print("==Graph==")
    for node in graph.nodes:
        print(node)
