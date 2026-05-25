"""Inventory management model."""

from dataclasses import dataclass, field
from typing import Iterable


def _empty_items() -> list[str]:
    """Create a typed empty list for dataclass default values."""
    return []


@dataclass
class Inventory:
    """Stores and manages player items."""

    items: list[str] = field(default_factory=_empty_items)

    def add(self, item_name: str) -> None:
        """Add an item to inventory if it is not already present."""
        if item_name not in self.items:
            self.items.append(item_name)

    def contains(self, item_name: str) -> bool:
        """Check whether the inventory includes an item."""
        return item_name in self.items

    def size(self) -> int:
        """Return the number of items in the inventory."""
        return len(self.items)

    def to_list(self) -> list[str]:
        """Return a copy of items for serialization/display."""
        return list(self.items)

    @classmethod
    def from_iterable(cls, values: Iterable[str]) -> "Inventory":
        """Build an inventory from any iterable of item strings."""
        return cls(items=list(values))
