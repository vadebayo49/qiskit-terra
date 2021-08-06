# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
A generic gate-inverse cancellation pass for a broad set of gate-inverse pairs.
"""

from qiskit.transpiler.basepasses import TransformationPass


class Cancellation(TransformationPass):
    """Cancel back-to-back `gates` in dag."""

    def __init__(self, gate_cancel):
        """Initialize gate_cancel"""
        self.gate_cancel = gate_cancel
        super().__init__()

    def run(self, dag):
        """Run the Cancellation pass on `dag`.

        Args:
            dag (DAGCircuit): the directed acyclic graph to run on.

        Returns:
            DAGCircuit: Transformed DAG.
        """
        gate_cancel_runs = dag.collect_runs(self.gate_cancel)
        # Generalize input using self.gate_cancel
        for gate_cancel_run in gate_cancel_runs:
            # Partition the gate_cancel_run into chunks with equal gate arguments
            partition = []
            chunk = []
            for i in range(len(gate_cancel_run) - 1):
                chunk.append(gate_cancel_run[i])

                qargs0 = gate_cancel_run[i].qargs
                qargs1 = gate_cancel_run[i + 1].qargs

                if qargs0 != qargs1:
                    partition.append(chunk)
                    chunk = []
            chunk.append(gate_cancel_run[-1])
            partition.append(chunk)
            # Simplify each chunk in the partition
            for chunk in partition:
                if len(chunk) % 2 == 0:
                    for n in chunk:
                        dag.remove_op_node(n)
                else:
                    for n in chunk[1:]:
                        dag.remove_op_node(n)
        return dag
