"""
game_state.py
-------------
Pure-Python (no GUI, no OpenCV) state machine for a round of the game.

Separating game state from the Tkinter view keeps the GUI thin and
testable - any UI we put in front of these methods will exhibit the same
behaviour.

Demonstrates: encapsulation (every attribute is private and exposed
through read-only properties), constructor, methods, and clean class
interaction with :class:`Difference`.
"""

from __future__ import annotations

from typing import List, Optional

from difference import Difference


class GameState:
    """Tracks score, mistakes and lockout across multiple images.

    Per-image counters (``mistakes``, ``locked``, ``remaining``) reset
    whenever a new image is loaded.  The cumulative *total found* counter
    keeps growing across the whole session.
    """

    #: Maximum incorrect guesses allowed per image.
    MAX_MISTAKES: int = 3

    def __init__(self) -> None:
        self._differences: List[Difference] = []
        self._mistakes: int = 0
        self._locked: bool = False
        self._total_found: int = 0  # cumulative across multiple images

    # ------------------------------------------------------------------ #
    # Round management.                                                  #
    # ------------------------------------------------------------------ #
    def reset_for_new_image(self, differences: List[Difference]) -> None:
        """Begin a new round with the supplied list of differences."""
        self._differences = differences
        self._mistakes = 0
        self._locked = False

    # ------------------------------------------------------------------ #
    # Click handling - the heart of the game loop.                       #
    # ------------------------------------------------------------------ #
    def register_click(self, x: int, y: int,
                       tolerance: int = 18) -> Optional[Difference]:
        """Process a click at ``(x, y)`` on the modified image.

        Returns
        -------
        Difference or None
            If the click landed on an unfound difference, that
            :class:`Difference` (now marked as found).  Otherwise
            ``None`` and the mistake counter is incremented.
        """
        if self._locked or not self._differences:
            return None

        for diff in self._differences:
            if not diff.found and diff.contains_point(x, y, tolerance):
                diff.mark_found()
                self._total_found += 1
                return diff

        # No hit - it's a miss.
        self._mistakes += 1
        if self._mistakes >= self.MAX_MISTAKES:
            self._locked = True
        return None

    def reveal_unfound(self) -> List[Difference]:
        """Mark every still-unfound difference as 'found' and return them.

        Called when the player presses the *Reveal* button.  Note that
        revealed differences do **not** count toward the cumulative
        score.
        """
        unfound = [d for d in self._differences if not d.found]
        for d in unfound:
            d.mark_found()
        # After a reveal the round is effectively over, so lock further
        # clicks - the player must load a new image to keep playing.
        self._locked = True
        return unfound

    # ------------------------------------------------------------------ #
    # Read-only properties (encapsulation).                              #
    # ------------------------------------------------------------------ #
    @property
    def mistakes(self) -> int:
        return self._mistakes

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def total_found(self) -> int:
        """Cumulative score across every image played in this session."""
        return self._total_found

    @property
    def remaining(self) -> int:
        """Differences in the *current* image that are still unfound."""
        return sum(1 for d in self._differences if not d.found)

    @property
    def differences(self) -> List[Difference]:
        return list(self._differences)

    @property
    def all_found(self) -> bool:
        return bool(self._differences) and self.remaining == 0
