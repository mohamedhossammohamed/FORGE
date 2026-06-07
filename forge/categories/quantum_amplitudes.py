"""
Category 24: Quantum State Amplitudes

Generates qubit state vectors subjected to quantum gates.
Difficulty scales from undergraduate (1 qubit, 2 gates) to frontier (3 qubits, 5 gates).
"""

import numpy as np
from fractions import Fraction
import sympy
from sympy import sqrt, Rational, Matrix, eye, zeros, exp, pi, I

from ..core.generator import ForgeCategory, Problem


class QuantumAmplitudesCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "quantum_amplitudes"
    
    @property
    def display_name(self) -> str:
        return "Quantum State Amplitudes"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n_qubits": 1, "n_gates": 2},
            2: {"n_qubits": 1, "n_gates": 3},
            3: {"n_qubits": 2, "n_gates": 3},
            4: {"n_qubits": 2, "n_gates": 4},
            5: {"n_qubits": 3, "n_gates": 5},
        }
        return params.get(difficulty, params[3])
    
    def _hadamard(self):
        """Hadamard gate: H = (1/√2) * [[1, 1], [1, -1]]"""
        return Matrix([
            [1, 1],
            [1, -1]
        ]) / sqrt(2)
    
    def _pauli_x(self):
        """Pauli-X gate: [[0, 1], [1, 0]]"""
        return Matrix([
            [0, 1],
            [1, 0]
        ])
    
    def _pauli_y(self):
        """Pauli-Y gate: [[0, -i], [i, 0]]"""
        return Matrix([
            [0, -I],
            [I, 0]
        ])
    
    def _pauli_z(self):
        """Pauli-Z gate: [[1, 0], [0, -1]]"""
        return Matrix([
            [1, 0],
            [0, -1]
        ])
    
    def _cnot(self):
        """CNOT gate (2-qubit): [[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]]"""
        return Matrix([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ])
    
    def _toffoli(self):
        """Toffoli gate (3-qubit): flips target if both controls are 1"""
        m = eye(8)
        # Swap |110> and |111>
        m[6, 6] = 0
        m[7, 7] = 0
        m[6, 7] = 1
        m[7, 6] = 1
        return m
    
    def _kronecker_product(self, A, B):
        """Compute Kronecker product of two matrices."""
        rows_a, cols_a = A.shape
        rows_b, cols_b = B.shape
        
        result = zeros(rows_a * rows_b, cols_a * cols_b)
        
        for i in range(rows_a):
            for j in range(cols_a):
                result[i*rows_b:(i+1)*rows_b, j*cols_b:(j+1)*cols_b] = A[i, j] * B
        
        return result
    
    def _get_gate(self, gate_name, rng, n_qubits=1):
        """Get a gate matrix by name, expanding to n_qubits if needed."""
        single_qubit_gates = {
            "H": self._hadamard(),
            "X": self._pauli_x(),
            "Y": self._pauli_y(),
            "Z": self._pauli_z(),
        }
        
        multi_qubit_gates = {
            "CNOT": self._cnot(),
            "Toffoli": self._toffoli(),
        }
        
        if gate_name in multi_qubit_gates:
            return multi_qubit_gates[gate_name]
        
        if gate_name in single_qubit_gates:
            gate = single_qubit_gates[gate_name]
            # Expand to n_qubits using Kronecker product with identity
            result = gate
            for _ in range(n_qubits - 1):
                result = self._kronecker_product(result, eye(2))
            return result
        
        return eye(2 ** n_qubits)
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_qubits = params["n_qubits"]
        n_gates = params["n_gates"]
        
        # Initial state |0...0>
        n_states = 2 ** n_qubits
        state = zeros(n_states, 1)
        state[0] = 1
        
        # Select gates
        single_gates = ["H", "X", "Y", "Z"]
        multi_gates = {
            2: ["CNOT"],
            3: ["Toffoli"],
        }
        
        gate_sequence = []
        for _ in range(n_gates):
            if n_qubits >= 2 and rng.random() < 0.3:
                # Only use multi-qubit gates if they match qubit count
                available_multi = multi_gates.get(n_qubits, [])
                if available_multi:
                    gate_name = available_multi[int(rng.integers(0, len(available_multi)))]
                else:
                    gate_name = single_gates[int(rng.integers(0, len(single_gates)))]
            else:
                gate_name = single_gates[int(rng.integers(0, len(single_gates)))]
            gate_sequence.append(gate_name)
        
        # Apply gates
        current_state = state
        for gate_name in gate_sequence:
            gate = self._get_gate(gate_name, rng, n_qubits)
            current_state = gate * current_state
        
        # Simplify
        current_state = current_state.applyfunc(lambda x: sympy.nsimplify(x, rational=False))
        
        # Format
        gate_str = " → ".join(gate_sequence)
        state_str = self._format_state(current_state, n_qubits)
        
        question = (
            f"A quantum system starts in the state |{'0' * n_qubits}>.\n\n"
            f"The following gates are applied in sequence:\n"
            f"{gate_str}\n\n"
            f"Compute the final state vector.\n"
            f"Provide the amplitudes as exact values (use √2 for sqrt(2), "
            f"and i for the imaginary unit)."
        )
        
        answer = state_str
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "n_qubits": n_qubits,
                "gate_sequence": gate_sequence,
                "initial_state": state.tolist(),
                "final_state": current_state.tolist(),
            },
        )
    
    def _format_state(self, state, n_qubits):
        """Format state vector as a string."""
        n_states = 2 ** n_qubits
        basis = [format(i, f'0{n_qubits}b') for i in range(n_states)]
        
        parts = []
        for i, (amp, basis_state) in enumerate(zip(state, basis)):
            if amp != 0:
                parts.append(f"{amp}|{basis_state}>")
        
        return " + ".join(parts) if parts else "0"
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade by checking state vector equivalence (up to global phase)."""
        try:
            # Parse both states
            pred_vec = self._parse_state_vector(prediction)
            ans_vec = self._parse_state_vector(answer)
            
            if pred_vec is None or ans_vec is None:
                return False
            
            if len(pred_vec) != len(ans_vec):
                return False
            
            # Check equivalence up to global phase
            # Find first non-zero amplitude
            ref_idx = None
            for i, amp in enumerate(ans_vec):
                if amp != 0:
                    ref_idx = i
                    break
            
            if ref_idx is None:
                return all(a == 0 for a in pred_vec)
            
            # Compute global phase
            if pred_vec[ref_idx] == 0:
                return False
            
            phase = ans_vec[ref_idx] / pred_vec[ref_idx]
            
            # Check all amplitudes match up to this phase
            for p, a in zip(pred_vec, ans_vec):
                if sympy.simplify(p * phase - a) != 0:
                    return False
            
            return True
        except:
            return False
    
    def _parse_state_vector(self, text: str):
        """Parse state vector from text representation."""
        try:
            # Simple parsing - extract amplitudes
            import re
            
            # Find all amplitude|basis> patterns
            pattern = r'([+-]?\s*(?:\d+(?:/\d+)?(?:\*?√?\d+)?)?)\s*\|([01]+)>'
            matches = re.findall(pattern, text)
            
            if not matches:
                return None
            
            n_qubits = len(matches[0][1])
            n_states = 2 ** n_qubits
            vec = [0] * n_states
            
            for amp_str, basis in matches:
                idx = int(basis, 2)
                amp_str = amp_str.strip().replace(' ', '')
                if amp_str in ('', '+'):
                    amp = 1
                elif amp_str == '-':
                    amp = -1
                else:
                    amp_str = amp_str.replace('√', 'sqrt').replace('*', '')
                    amp = sympy.sympify(amp_str)
                vec[idx] = amp
            
            return vec
        except:
            return None
