"""
difference.py
-------------
Defines the ``Difference`` class which represents a single hidden difference
region inside a modified image.

Demonstrates:
    * Encapsulation - all attributes are private (``_name``); access is
      provided via ``@property`` accessors so external classes can read the
      state but never accidentally mutate it.
    * Constructor (``__init__``) that fully initialises a region.
    * Class interaction - ``Difference`` instances are stored and queried by
      ``ImageProcessor`` and ``GameState``.

Author: HIT137 Group Assignment 3, Semester 1 2026.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


class Difference:
    """A rectangular region of the cloned image that has been altered.

    Each instance stores the bounding box (``x``, ``y``, ``w``, ``h``), the
    name of the alteration that was applied (e.g. ``"blur"``), and whether
    the player has already located the region.

    The class is responsible for two pieces of game logic:

    1. ``contains_point`` - test whether a player click falls inside the
       region (with a configurable tolerance).
    2. ``overlaps`` - test whether two prospective regions overlap, used by
       :class:`ImageProcessor` to guarantee non-overlapping difference
       placement.
    """

    __slots__ = ("_x", "_y", "_w", "_h", "_alteration_type", "_found")

    def __init__(self, x: int, y: int, w: int, h: int,
                 alteration_type: str = "") -> None:
        # All attributes are name-mangled / private (encapsulation).
        self._x = int(x)
        self._y = int(y)
        self._w = int(w)
        self._h = int(h)
        self._alteration_type = alteration_type
        self._found = False

    # ------------------------------------------------------------------ #
    # Read-only properties - external code uses these to access state.    #
    # ------------------------------------------------------------------ #
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Return the bounding box ``(x, y, w, h)``."""
        return self._x, self._y, self._w, self._h

    @property
    def center(self) -> Tuple[int, int]:
        """Return the centre ``(cx, cy)`` of the region."""
        return self._x + self._w // 2, self._y + self._h // 2

    @property
    def radius(self) -> int:
        """Return a radius large enough to fully circumscribe the region."""
        return max(self._w, self._h) // 2 + 8

    @property
    def alteration_type(self) -> str:
        """Return the name of the alteration applied to the region."""
        return self._alteration_type

    @property
    def found(self) -> bool:
        """Return ``True`` if the player has already located this region."""
        return self._found

    # ------------------------------------------------------------------ #
    # State-changing methods.                                            #
    # ------------------------------------------------------------------ #
    def mark_found(self) -> None:
        """Flag this region as discovered by the player."""
        self._found = True

    # ------------------------------------------------------------------ #
    # Geometry helpers.                                                  #
    # ------------------------------------------------------------------ #
    def contains_point(self, px: int, py: int, tolerance: int = 18) -> bool:
        """Return ``True`` if ``(px, py)`` is within ``tolerance`` of the region.

        Uses an *inflated bounding-box* test - the click only has to land
        near the region, not exactly on it, which matches the assignment
        spec ("reasonable proximity to any unfound difference region").
        """
        return (
            self._x - tolerance <= px <= self._x + self._w + tolerance
            and self._y - tolerance <= py <= self._y + self._h + tolerance
        )

    def overlaps(self, other: "Difference", margin: int = 4) -> bool:
        """Axis-aligned bounding-box overlap test (with safety ``margin``)."""
        return not (
            self._x + self._w + margin < other._x
            or other._x + other._w + margin < self._x
            or self._y + self._h + margin < other._y
            or other._y + other._h + margin < self._y
        )

    # ------------------------------------------------------------------ #
    # Debug representation.                                              #
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (f"Difference(x={self._x}, y={self._y}, "
                f"w={self._w}, h={self._h}, type={self._alteration_type!r}, "
                f"found={self._found})")
