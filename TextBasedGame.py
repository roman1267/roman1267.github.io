"""Roman Maciel."""

import time


def show_status(current_room, inventory, items):
    """Display the player's current status."""
    # Save the game state as strings for easier calculations
    room_string = "| You are in the {} ".format(current_room)
    inventory_string = "| Inventory: {} ".format(
        ", ".join(inventory) if inventory else "Empty"
    )

    # Pad status info depending on which string is longer
    if len(room_string) > len(inventory_string):
        for i in range(len(room_string) + 1):
            print("_", end="")
        for i in range(len(room_string) - len(inventory_string)):
            inventory_string += " "
        inventory_string += "|"
        room_string += "|"
    else:
        for i in range(len(inventory_string) - len(room_string)):
            room_string += " "
        room_string += "|"
        inventory_string += "|"
        for i in range(len(inventory_string)):
            print("_", end="")

    print()
    print(room_string)
    print("|", end="")

    # Separator padding between room and status
    if len(room_string) > len(inventory_string):
        for i in range(len(room_string) - 2):
            print("_", end="")
    else:
        for i in range(len(inventory_string) - 2):
            print("_", end="")

    print("|")
    print(inventory_string)
    print("|", end="")

    # More padding
    if len(room_string) > len(inventory_string):
        for i in range(len(room_string) - 2):
            print("_", end="")
    else:
        for i in range(len(inventory_string) - 2):
            print("_", end="")
    print("|\n")

    # Display item if it exists in the room
    if items[current_room]:
        print("[You see a {} here]".format(items[current_room]))
    else:
        print("[There are no items in this room]")


def main():
    """Create the main game loop and initialize the game state."""
    # Room and item dictionaries
    rooms = {
        "Entrance Hall": {
            "North": "Dining Room",
            "East": "Master Bedroom",
            "South": "Library",
            "West": "Garden",
        },
        "Library": {"North": "Entrance Hall", "East": "Basement"},
        "Dining Room": {"South": "Entrance Hall", "East": "Kitchen"},
        "Kitchen": {"West": "Dining Room"},
        "Basement": {"West": "Library"},
        "Master Bedroom": {"West": "Entrance Hall", "North": "Attic"},
        "Attic": {},
        "Garden": {"East": "Entrance Hall"},
    }

    items = {
        "Entrance Hall": "Crystal Orb",
        "Library": "Key",
        "Dining Room": "Cursed Amulet",
        "Kitchen": "Silver Knife",
        "Basement": "Lantern of Shadows",
        "Master Bedroom": "Golden Ring",
        "Attic": None,  # Villain room
        "Garden": None,  # Starting room
    }

    # Establish starting game state
    inventory = []
    current_room = "Garden"

    print(
        "Welcome to Haunted Mansion Escape! Collect all the items to win the game. Avoid the Phantom of Despair until you have all the items!\n"
    )

    # Main game loop
    while True:
        # UX time padding
        time.sleep(0.7)

        # Show status
        show_status(current_room, inventory, items)

        # Prompt player for input
        command = (
            input("\n> Enter a command (e.g., 'go North' or 'get [item]'): ")
            .strip()
            .split()
        )

        print()
        time.sleep(0.7)

        # Handle empty command
        if len(command) == 0:
            print("> Please enter a command.\n")
            continue

        # Handle directional command
        if command[0].lower() == "go":
            if len(command) < 2:
                print("> Go where? Specify a direction (North, South, East, West).\n")
                continue

            direction = command[1].capitalize()
            # Ensure direction is valid for current room
            if direction in rooms[current_room]:
                current_room = rooms[current_room][direction]
                # Check for ending room
                if current_room == "Attic":
                    if len(inventory) == 6:
                        print(
                            "\n> Congratulations! You have collected all items and defeated the Phantom of Despair!"
                        )
                        break
                    else:
                        print(
                            "\n> You encountered the Phantom of Despair without all items! GAME OVER!"
                        )
                        break
                continue
            else:
                print("> You can't go that way!")

        # Handle get command
        elif command[0].lower() == "get":
            # Ensure item is specified
            if len(command) < 2:
                print("> Get what? Specify the item name.\n")
                continue

            item_name = " ".join(command[1:])
            # Make sure item is present in current room
            if items[current_room] == item_name:
                inventory.append(item_name)
                items[current_room] = None
                print("> {} retrieved!".format(item_name))
            else:
                print("> There's no such item here!")

        else:
            print("> Invalid command! Use 'go [direction]' or 'get [item]'.")
        print()


if __name__ == "__main__":
    main()
