"""Graph structure and traversal algorithms for world navigation."""

from __future__ import annotations

from collections import deque


def _normalize(value: str) -> str:
	return " ".join(value.strip().lower().split())


class WorldGraph:
	"""Represents the game world as a directed graph with labeled edges."""

	def __init__(self) -> None:
		self._adjacency: dict[str, dict[str, str]] = {}
		self._room_lookup: dict[str, str] = {}

	def add_room(self, room_name: str) -> None:
		"""Register a room vertex if it has not been seen before."""
		if room_name not in self._adjacency:
			self._adjacency[room_name] = {}
			self._room_lookup[_normalize(room_name)] = room_name

	def add_edge(self, room_name: str, direction: str, destination_name: str) -> None:
		"""Create/update a directional edge to another room."""
		self.add_room(room_name)
		self.add_room(destination_name)
		self._adjacency[room_name][direction] = destination_name

	def room_exists(self, room_name: str) -> bool:
		"""Check whether a canonical room name exists in the graph."""
		return room_name in self._adjacency

	def resolve_room_name(self, raw_name: str) -> str | None:
		"""Resolve user-provided room text to canonical room names."""
		return self._room_lookup.get(_normalize(raw_name))

	def can_move(self, room_name: str, direction: str) -> bool:
		"""Return True when a labeled edge exists from a room."""
		exits = self._adjacency.get(room_name)
		if exits is None:
			return False
		return direction in exits

	def next_room(self, room_name: str, direction: str) -> str | None:
		"""Return destination room for a direction edge."""
		exits = self._adjacency.get(room_name)
		if exits is None:
			return None
		return exits.get(direction)

	def directions_from(self, room_name: str) -> dict[str, str]:
		"""Return a copy of outgoing edges for a room."""
		return dict(self._adjacency.get(room_name, {}))

	def shortest_path_rooms(self, start_room: str, target_room: str) -> list[str]:
		"""Find shortest room path using BFS on unweighted graph."""
		if start_room == target_room:
			return [start_room]

		if start_room not in self._adjacency or target_room not in self._adjacency:
			return []

		queue: deque[str] = deque([start_room])
		parents: dict[str, str | None] = {start_room: None}

		while queue:
			current = queue.popleft()
			for destination in self._adjacency[current].values():
				if destination in parents:
					continue

				parents[destination] = current
				if destination == target_room:
					return self._reconstruct_room_path(parents, target_room)
				queue.append(destination)

		return []

	def shortest_path_directions(self, start_room: str, target_room: str) -> list[str]:
		"""Find shortest direction sequence from start room to target room."""
		room_path = self.shortest_path_rooms(start_room, target_room)
		if len(room_path) < 2:
			return []

		directions: list[str] = []
		for index in range(len(room_path) - 1):
			source = room_path[index]
			destination = room_path[index + 1]
			exit_map = self._adjacency[source]
			direction = next(
				(edge_direction for edge_direction, edge_destination in exit_map.items() if edge_destination == destination),
				None,
			)
			if direction is None:
				return []
			directions.append(direction)

		return directions

	@staticmethod
	def _reconstruct_room_path(parents: dict[str, str | None], target_room: str) -> list[str]:
		"""Reconstruct path from parent map produced by BFS."""
		path: list[str] = []
		cursor: str | None = target_room
		while cursor is not None:
			path.append(cursor)
			cursor = parents.get(cursor)
		path.reverse()
		return path
