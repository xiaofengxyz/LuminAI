from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowNode:
    id: str
    system: str
    payload: dict[str, Any] = field(default_factory=dict)


class WorkflowGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, WorkflowNode] = {}
        self.edges: dict[str, set[str]] = {}

    def add_node(self, node: WorkflowNode) -> None:
        self.nodes[node.id] = node
        self.edges.setdefault(node.id, set())

    def connect(self, source_id: str, target_id: str) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError("Both workflow nodes must exist before connecting them")
        self.edges.setdefault(source_id, set()).add(target_id)

    def topological_order(self) -> list[WorkflowNode]:
        incoming = {node_id: 0 for node_id in self.nodes}
        for targets in self.edges.values():
            for target in targets:
                incoming[target] += 1
        ready = [node_id for node_id, count in incoming.items() if count == 0]
        ordered: list[WorkflowNode] = []
        while ready:
            node_id = ready.pop(0)
            ordered.append(self.nodes[node_id])
            for target in sorted(self.edges.get(node_id, set())):
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
        if len(ordered) != len(self.nodes):
            raise ValueError("Workflow graph contains a cycle")
        return ordered
