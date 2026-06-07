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
        """
        Grade by checking state vector equivalence (up to global phase).

        Parsing priority:
        1. JSON array of complex numbers  e.g. [0.707, 0, 0, 0.707]
        2. Ket notation with symbolic amplitudes  e.g. (1/√2)|00> + (1/√2)|11>
        3. Comma-separated complex / float values
        """
        try:
            pred_vec = self._parse_state_vector(prediction)
            ans_vec = self._parse_state_vector(answer)

            if pred_vec is None or ans_vec is None:
                return False
            if len(pred_vec) != len(ans_vec):
                return False

            tol = 1e-4

            def to_complex(v):
                try:
                    return complex(sympy.N(v, 15))
                except Exception:
                    return complex(v)

            pred_c = [to_complex(x) for x in pred_vec]
            ans_c = [to_complex(x) for x in ans_vec]

            # Find first non-zero answer amplitude
            ref_idx = next((i for i, a in enumerate(ans_c) if abs(a) > tol), None)
            if ref_idx is None:
                return all(abs(p) < tol for p in pred_c)

            if abs(pred_c[ref_idx]) < tol:
                return False

            # Global phase factor
            phase = ans_c[ref_idx] / pred_c[ref_idx]

            for p, a in zip(pred_c, ans_c):
                if abs(p * phase - a) > tol:
                    return False
            return True
        except Exception:
            return False

    def _parse_state_vector(self, text: str):
        """
        Parse a quantum state vector from a string.

        Handles (in order of preference):
        1. JSON array: [0.707, 0, 0, 0.707]  or  [[0.707,0],[0,0],[0,0],[0.707,0]]
        2. Ket notation: (1/√2)|00> + (1/√2)|11>
        3. Comma-separated complex / float values: 0.707+0j, 0, 0, 0.707
        """
        import re
        import json

        text = text.strip()

        # ── Path 1: JSON array ──────────────────────────────────────────────
        json_match = re.search(r'\[[\d\s.,+\-ej\[\]]+\]', text, re.IGNORECASE)
        if json_match:
            try:
                raw = json.loads(json_match.group())
                vec = []
                for item in raw:
                    if isinstance(item, list):
                        vec.append(complex(item[0], item[1] if len(item) > 1 else 0))
                    else:
                        vec.append(complex(item))
                if vec:
                    return [sympy.sympify(v) for v in vec]
            except Exception:
                pass

        # ── Path 2: Ket notation ────────────────────────────────────────────
        # Matches: (1/√2)|00>  or  -1/2|1>  or  |0>  or  -(1/√2)|1>
        ket_pattern = re.compile(
            r'([+\-]?\s*'
            r'(?:\([^)]*\)|[\d√/.*\s]+)?'
            r')\s*\|([01]+)>',
            re.UNICODE,
        )
        matches = ket_pattern.findall(text)
        if matches:
            n_qubits = len(matches[0][1])
            n_states = 2 ** n_qubits
            vec = [sympy.Integer(0)] * n_states

            for amp_raw, basis in matches:
                idx = int(basis, 2)
                amp_str = amp_raw.strip().replace(' ', '')

                if amp_str.startswith('(') and amp_str.endswith(')'):
                    amp_str = amp_str[1:-1]

                if amp_str in ('', '+'):
                    amp = sympy.Integer(1)
                elif amp_str == '-':
                    amp = sympy.Integer(-1)
                else:
                    amp_str = (
                        amp_str
                        .replace('√', 'sqrt')
                        .replace('i', 'I')
                        .replace('j', 'I')
                    )
                    try:
                        amp = sympy.sympify(amp_str)
                    except Exception:
                        amp = sympy.Integer(0)

                vec[idx] = vec[idx] + amp

            return vec

        # ── Path 3: Comma-separated complex / float values ──────────────────
        parts = [p.strip() for p in re.split(r',\s*', text) if p.strip()]
        if len(parts) >= 2:
            vec = []
            for p in parts:
                p = p.replace('i', 'j')
                try:
                    vec.append(sympy.sympify(complex(p)))
                except Exception:
                    try:
                        vec.append(sympy.sympify(p))
                    except Exception:
                        vec = []
                        break
            if vec:
                return vec

        return None
