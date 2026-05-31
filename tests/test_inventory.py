from inventory import Inventory


def test_inventory_tracks_order_and_counts() -> None:
    inventory = Inventory()
    inventory.add("Lantern of Shadows")
    inventory.add("Crystal Orb")
    inventory.add("Lantern of Shadows")

    assert inventory.count("Lantern of Shadows") == 2
    assert inventory.count("Crystal Orb") == 1
    assert inventory.to_list() == ["Lantern of Shadows", "Crystal Orb"]
    assert inventory.to_detailed_list() == ["Lantern of Shadows x2", "Crystal Orb"]


def test_inventory_remove_updates_unique_size() -> None:
    inventory = Inventory.from_iterable(["Key", "Key", "Golden Ring"])

    assert inventory.size() == 2
    assert inventory.total_items() == 3

    assert inventory.remove("Key", 1) is True
    assert inventory.count("Key") == 1
    assert inventory.size() == 2

    assert inventory.remove("Key", 1) is True
    assert inventory.contains("Key") is False
    assert inventory.size() == 1
