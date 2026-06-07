"""
Category 8: Graph Theory - Shortest Path

Generates random graphs with integer edge weights and computes shortest paths.
Difficulty scales from high school (small graphs) to frontier (large dense graphs).
"""

import numpy as np

from ..core.generator import ForgeCategory, Problem


class GraphShortestPathCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "graph_shortest_path"
    
    @property
    def display_name(self) -> str:
        return "Graph Theory: Shortest Path"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n_vertices": (4, 6), "edge_density": 0.5, "weight_range": (1, 10)},
            2: {"n_vertices": (6, 10), "edge_density": 0.4, "weight_range": (1, 20)},
            3: {"n_vertices": (10, 15), "edge_density": 0.3, "weight_range": (1, 50)},
            4: {"n_vertices": (15, 20), "edge_density": 0.3, "weight_range": (1, 100)},
            5: {"n_vertices": (20, 30), "edge_density": 0.25, "weight_range": (1, 200)},
        }
        return params.get(difficulty, params[3])
    
    def _dijkstra(self, graph, start, end):
        """Dijkstra's algorithm for shortest path."""
        import heapq
        
        n = len(graph)
        dist = [float('inf')] * n
        dist[start] = 0
        prev = [None] * n
        pq = [(0, start)]
        
        while pq:
            d, u = heapq.heappop(pq)
            
            if d > dist[u]:
                continue
            
            if u == end:
                break
            
            for v, weight in graph[u]:
                new_dist = d + weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))
        
        # Reconstruct path
        if dist[end] == float('inf'):
            return None, float('inf')
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = prev[current]
        path.reverse()
        
        return path, dist[end]
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n = int(rng.integers(*params["n_vertices"]))
        edge_density = params["edge_density"]
        weight_range = params["weight_range"]
        
        # Generate adjacency list
        graph = [[] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < edge_density:
                    weight = int(rng.integers(*weight_range))
                    graph[i].append((j, weight))
                    graph[j].append((i, weight))
        
        # Ensure connectivity by adding a spanning tree
        visited = {0}
        while len(visited) < n:
            u = list(visited)[int(rng.integers(0, len(visited)))]
            v_candidates = [v for v in range(n) if v not in visited]
            if v_candidates:
                v = v_candidates[int(rng.integers(0, len(v_candidates)))]
                weight = int(rng.integers(*weight_range))
                graph[u].append((v, weight))
                graph[v].append((u, weight))
                visited.add(v)
        
        # Choose start and end
        start = 0
        end = n - 1
        
        # Compute shortest path
        path, distance = self._dijkstra(graph, start, end)
        
        # Format graph as adjacency list
        adj_str = ""
        for i in range(n):
            neighbors = ", ".join(f"{v}(w={w})" for v, w in graph[i])
            adj_str += f"  {i}: {neighbors}\n"
        
        question = (
            f"Find the shortest path distance from vertex {start} to vertex {end} "
            f"in the following weighted graph:\n\n"
            f"Adjacency list (vertex: neighbor(weight)):\n{adj_str}\n"
            f"Provide the total weight of the shortest path as an integer."
        )
        
        answer = distance
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "graph": graph,
                "start": start,
                "end": end,
                "path": path,
                "distance": distance,
            },
        )
    
    def grade(self, prediction: str, answer: int) -> bool:
        try:
            pred = prediction.strip().replace(',', '').replace(' ', '')
            return int(pred) == int(answer)
        except (ValueError, TypeError):
            return False
