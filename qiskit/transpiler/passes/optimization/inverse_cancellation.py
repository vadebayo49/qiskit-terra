# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
A generic gate-inverse cancellation pass for any set of gate-inverse pairs.
"""
from typing import List, Tuple, Union

from qiskit.circuit import Gate
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError


class Cancellation(TransformationPass):
    """Cancel specific Gates which are inverses of each other when they occur back-to-
    back."""

    def __init__(self, gates_to_cancel: List[Union[Gate, Tuple[Gate, Gate]]]):
        """Initialize Cancellation pass.

        Args:
            gates_to_cancel: list of gates to cancel

        Raises:
            TranspilerError:
                Initalization raises an error when the input is not a self-inverse gate
                or a two-tuple of inverse gates.
        """
        for gates in gates_to_cancel:
            if isinstance(gates, Gate):
                if gates != gates.inverse():
                    raise TranspilerError("Gate {} is not self-inverse".format(gates.name))
            elif isinstance(gates, tuple):
                if len(gates) != 2:
                    raise TranspilerError(
                        "Too many or too few inputs: {}. Only two are allowed.".format(gates)
                    )
                elif gates[0] != gates[1].inverse():
                    raise TranspilerError(
                        "Gate {} and {} are not inverse.".format(gates[0].name, gates[1].name)
                    )
            else:
                raise TranspilerError(
                    "Cancellation pass does not take input type {}. Input must be"
                    " a Gate.".format(type(gates))
                )

        self.gates_to_cancel = gates_to_cancel
        super().__init__()

    def run(self, dag: DAGCircuit):
        """Run the Cancellation pass on `dag`.

        Args:
            dag: the directed acyclic graph to run on.

        Returns:
            DAGCircuit: Transformed DAG.
        """
        self_inverse_gates = []
        inverse_gate_pairs = []

        for gates in self.gates_to_cancel:
            if isinstance(gates, Gate):
                self_inverse_gates.append(gates)
            else:
                inverse_gate_pairs.append(gates)

        dag = self._run_on_self_inverse(dag, self_inverse_gates)
        return self._run_on_inverse_pairs(dag, inverse_gate_pairs)

    def _run_on_self_inverse(self, dag: DAGCircuit, self_inverse_gates: List[Gate]):
        """
        Run self-inverse gates on `dag`.

        Args:
            dag: the directed acyclic graph to run on.
            self_inverse_gates: list of gates who cancel themeselves in pairs

        Returns:
            DAGCircuit: Transformed DAG.
        """
        gate_cancel_runs = dag.collect_runs([gate.name for gate in self_inverse_gates])
        for gate_cancel_run in gate_cancel_runs:
            partitions = []
            chunk = []
            for i in range(len(gate_cancel_run) - 1):
                chunk.append(gate_cancel_run[i])
                if gate_cancel_run[i].qargs != gate_cancel_run[i + 1].qargs:
                    partitions.append(chunk)
                    chunk = []
            chunk.append(gate_cancel_run[-1])
            partitions.append(chunk)
            # Remove an even number of gates from each chunk
            for chunk in partitions:
                if len(chunk) % 2 == 0:
                    dag.remove_op_node(chunk[0])
                for node in chunk[1:]:
                    dag.remove_op_node(node)
        return dag

    def _run_on_inverse_pairs(self, dag: DAGCircuit, inverse_gate_pairs: List[Tuple[Gate, Gate]]):
        """
        Run inverse gate pairs on `dag`.

        Args:
            dag: the directed acyclic graph to run on.
            inverse_gate_pairs: list of gates with inverse angles that cancel each other.

        Returns:
            DAGCircuit: Transformed DAG.
        """
        for pair in inverse_gate_pairs:
            gate_cancel_runs = dag.collect_runs([pair[0].name])
            for dag_nodes in gate_cancel_runs:
                for i in range(len(dag_nodes) - 1):
                    if dag_nodes[i].op == pair[0] and dag_nodes[i + 1].op == pair[1]:
                        dag.remove_op_node(dag_nodes[i])
                        dag.remove_op_node(dag_nodes[i + 1])
                    elif dag_nodes[i].op == pair[1] and dag_nodes[i + 1].op == pair[0]:
                        dag.remove_op_node(dag_nodes[i])
                        dag.remove_op_node(dag_nodes[i + 1])

        return dag
