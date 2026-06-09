"""Inventory management model."""

from dataclasses import dataclass, field
from typing import Iterable


def _empty_counts() -> dict[str, int]:
    """Create default item-count lookup storage."""
    return {}


def _empty_order() -> list[str]:
    """Create default stable item insertion order."""
    return []


@dataclass
class Inventory:
    """Stores items using fast lookup and stable display ordering."""

    item_counts: dict[str, int] = field(default_factory=_empty_counts)
    item_order: list[str] = field(default_factory=_empty_order)

    def add(self, item_name: str, quantity: int = 1) -> None:
        """Add quantity for item and keep first-seen ordering."""
        if quantity <= 0:
            return

        if item_name not in self.item_counts:
            self.item_order.append(item_name)
            self.item_counts[item_name] = 0

        self.item_counts[item_name] += quantity

    def remove(self, item_name: str, quantity: int = 1) -> bool:
        """Remove quantity for item if present; return True when successful."""
        if quantity <= 0:
            return True

        current = self.item_counts.get(item_name, 0)
        if current < quantity:
            return False

        remaining = current - quantity
        if remaining == 0:
            del self.item_counts[item_name]
            self.item_order = [name for name in self.item_order if name != item_name]
        else:
            self.item_counts[item_name] = remaining
        return True

    def contains(self, item_name: str) -> bool:
        """Check whether the inventory includes at least one of an item."""
        return self.item_counts.get(item_name, 0) > 0

    def count(self, item_name: str) -> int:
        """Return how many copies of an item are held."""
        return self.item_counts.get(item_name, 0)

    def size(self) -> int:
        """Return unique item count (used for progression checks)."""
        return len(self.item_order)

    def total_items(self) -> int:
        """Return total quantity across all items."""
        return sum(self.item_counts.values())

    def to_list(self) -> list[str]:
        """Return stable ordered item names for serialization/display."""
        return [item for item in self.item_order if self.item_counts.get(item, 0) > 0]

    def to_detailed_list(self) -> list[str]:
        """Return ordered display values including quantities where needed."""
        values: list[str] = []
        for item in self.to_list():
            qty = self.item_counts[item]
            if qty <= 1:
                values.append(item)
            else:
                values.append(f"{item} x{qty}")
        return values

    @classmethod
    def from_iterable(cls, values: Iterable[str]) -> "Inventory":
        """Build inventory from iterable values, preserving order and counts."""
        inventory = cls()
        for value in values:
            inventory.add(str(value))
        return inventory
