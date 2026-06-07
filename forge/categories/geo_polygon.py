"""
Category 18: Geometry - Polygon Properties

Generates random coordinate vertices forming simple polygons and computes area.
Difficulty scales from middle school (3 vertices) to frontier (12 vertices, highly concave).
"""

from fractions import Fraction

from ..core.generator import ForgeCategory, Problem


class GeoPolygonCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "geo_polygon"
    
    @property
    def display_name(self) -> str:
        return "Geometry: Polygon Properties"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n_vertices": 3, "coord_range": (-10, 10), "ensure_concave": False},
            2: {"n_vertices": 4, "coord_range": (-20, 20), "ensure_concave": False},
            3: {"n_vertices": 5, "coord_range": (-30, 30), "ensure_concave": False},
            4: {"n_vertices": 8, "coord_range": (-50, 50), "ensure_concave": True},
            5: {"n_vertices": 12, "coord_range": (-100, 100), "ensure_concave": True},
        }
        return params.get(difficulty, params[3])
    
    def _sort_vertices_radially(self, vertices):
        """Sort vertices in counter-clockwise order to ensure simple polygon."""
        # Compute centroid
        cx = sum(v[0] for v in vertices) / len(vertices)
        cy = sum(v[1] for v in vertices) / len(vertices)
        
        # Sort by angle from centroid
        import math
        def angle(v):
            return math.atan2(v[1] - cy, v[0] - cx)
        
        return sorted(vertices, key=angle)
    
    def _shoelace_area(self, vertices):
        """Compute area using the Shoelace formula."""
        n = len(vertices)
        area = Fraction(0)
        
        for i in range(n):
            j = (i + 1) % n
            area += Fraction(vertices[i][0]) * Fraction(vertices[j][1])
            area -= Fraction(vertices[j][0]) * Fraction(vertices[i][1])
        
        return abs(area) / 2
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_vertices = params["n_vertices"]
        coord_range = params["coord_range"]
        
        # Generate vertices
        vertices = []
        for _ in range(n_vertices):
            x = int(rng.integers(*coord_range))
            y = int(rng.integers(*coord_range))
            vertices.append((x, y))
        
        # Sort radially to ensure simple polygon
        vertices = self._sort_vertices_radially(vertices)
        
        # Compute area
        area = self._shoelace_area(vertices)
        
        # Format vertices
        vertices_str = ", ".join(f"({x}, {y})" for x, y in vertices)
        
        question = (
            f"Compute the area of the polygon with the following vertices "
            f"(in order):\n\n"
            f"{vertices_str}\n\n"
            f"Use the Shoelace formula: A = ½|Σ(x_i·y_{{i+1}} - x_{{i+1}}·y_i)|\n"
            f"Provide the exact area as a fraction if it's not an integer."
        )
        
        if area.denominator == 1:
            answer = int(area)
        else:
            answer = str(area)
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"vertices": vertices, "area": str(area)},
        )
    
    def grade(self, prediction: str, answer) -> bool:
        try:
            from fractions import Fraction
            
            pred = prediction.strip().replace(',', '')
            
            if isinstance(answer, int):
                if '/' in pred:
                    frac = Fraction(pred)
                    return frac.denominator == 1 and frac.numerator == answer
                return int(float(pred)) == answer
            else:
                target = Fraction(answer)
                if '/' in pred:
                    return Fraction(pred) == target
                try:
                    return float(pred) == float(target)
                except:
                    return False
        except (ValueError, TypeError):
            return False
