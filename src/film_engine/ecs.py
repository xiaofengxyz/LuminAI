from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Component:
    kind: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    id: str
    kind: str
    components: dict[str, Component] = field(default_factory=dict)

    def add_component(self, component: Component) -> None:
        self.components[component.kind] = component

    def get_component(self, kind: str) -> Component | None:
        return self.components.get(kind)


class EntityRegistry:
    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}

    def create(self, kind: str, entity_id: str | None = None) -> Entity:
        entity = Entity(id=entity_id or str(uuid.uuid4()), kind=kind)
        self._entities[entity.id] = entity
        return entity

    def add(self, entity: Entity) -> Entity:
        self._entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def by_kind(self, kind: str) -> list[Entity]:
        return [entity for entity in self._entities.values() if entity.kind == kind]

    def all(self) -> list[Entity]:
        return list(self._entities.values())
