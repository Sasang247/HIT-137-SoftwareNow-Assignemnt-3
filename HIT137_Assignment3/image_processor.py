"""
image_processor.py
------------------
Loads images from disk, clones them, and programmatically introduces
exactly *five* non-overlapping, randomly-positioned, randomly-typed
differences into the clone.

Pure OpenCV is used for **all** pixel manipulation (file load, resize,
colour-space conversion and the alteration kernels in
:mod:`alterations`) - no PIL/Pillow operations beyond the final Tkinter
conversion in :mod:`app`.

Class responsibilities:
    * :class:`ImageProcessor` - file IO, scaling, region generation and
      coordinating polymorphic :class:`Alteration` objects.

Demonstrates: encapsulation, constructor, methods, class interaction.
"""

from __future__ import annotations

import random
from typing import List, Tuple

import cv2
import numpy as np

from alterations import ALL_ALTERATIONS, Alteration
from difference import Difference


class ImageProcessor:
    """Load an image and generate a tampered twin with hidden differences."""

    #: Exact number of differences the assignment requires.
    NUM_DIFFERENCES: int = 5

    #: Hard upper bound on placement attempts before giving up.
    _MAX_ATTEMPTS: int = 1000

    def __init__(self, max_size: Tuple[int, int] = (720, 620)) -> None:
        """Create a new processor.

        Parameters
        ----------
        max_size
            ``(max_width, max_height)`` that the loaded image will be
            scaled down to (while preserving aspect ratio).  Images
            smaller than this are not enlarged.
        """
        self._max_w, self._max_h = max_size
        self._original: np.ndarray | None = None
        self._modified: np.ndarray | None = None
        self._differences: List[Difference] = []

    # ------------------------------------------------------------------ #
    # Public API.                                                        #
    # ------------------------------------------------------------------ #
    def load_image(self, path: str) -> np.ndarray:
        """Read ``path`` from disk and store a scaled-to-fit copy."""
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(
                f"Unable to load image: '{path}'. "
                "Make sure the file exists and is a JPG, PNG, or BMP."
            )
        self._original = self._scale_to_fit(img)
        # Reset any prior state.
        self._modified = None
        self._differences = []
        return self._original

    def generate_differences(self) -> Tuple[np.ndarray, List[Difference]]:
        """Clone the original and inject 5 non-overlapping alterations.

        Returns
        -------
        modified : numpy.ndarray
            The tampered image (BGR).
        differences : list[Difference]
            Metadata for every region that was altered.

        Raises
        ------
        RuntimeError
            If no image has been loaded yet, or if 5 non-overlapping
            regions could not be placed.
        """
        if self._original is None:
            raise RuntimeError("Load an image before generating differences.")

        # All alterations happen on a *deep clone*; the original is
        # untouched and kept for the left-hand display.
        self._modified = self._original.copy()
        self._differences = []

        h, w = self._original.shape[:2]
        # Region sizes scale with image dimensions - this keeps them
        # subtle on small images and not enormous on big ones.
        rw_min, rw_max = int(w * 0.06), int(w * 0.13)
        rh_min, rh_max = int(h * 0.06), int(h * 0.13)

        attempts = 0
        while (len(self._differences) < self.NUM_DIFFERENCES
               and attempts < self._MAX_ATTEMPTS):
            attempts += 1

            rw = random.randint(rw_min, rw_max)
            rh = random.randint(rh_min, rh_max)
            rx = random.randint(8, w - rw - 8)
            ry = random.randint(8, h - rh - 8)
            candidate = Difference(rx, ry, rw, rh)

            # Guarantee non-overlap.
            if any(candidate.overlaps(d) for d in self._differences):
                continue

            alteration_cls = random.choice(ALL_ALTERATIONS)
            alteration: Alteration = alteration_cls()
            alteration(self._modified, rx, ry, rw, rh)  # polymorphic call

            # Re-create the Difference, this time tagging the alteration.
            self._differences.append(
                Difference(rx, ry, rw, rh, alteration.display_name)
            )

        if len(self._differences) < self.NUM_DIFFERENCES:
            raise RuntimeError(
                "Could not place 5 non-overlapping regions on this image. "
                "Try a larger image."
            )

        return self._modified, self._differences

    # ------------------------------------------------------------------ #
    # Internal helpers.                                                  #
    # ------------------------------------------------------------------ #
    def _scale_to_fit(self, img: np.ndarray) -> np.ndarray:
        """Return ``img`` resized so it fits inside the configured bounds.

        Aspect ratio is preserved; images already smaller than the bounds
        are returned untouched.
        """
        h, w = img.shape[:2]
        scale = min(self._max_w / w, self._max_h / h, 1.0)
        if scale >= 1.0:
            return img
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # ------------------------------------------------------------------ #
    # Encapsulated read-only state.                                      #
    # ------------------------------------------------------------------ #
    @property
    def original(self) -> np.ndarray | None:
        return self._original

    @property
    def modified(self) -> np.ndarray | None:
        return self._modified

    @property
    def differences(self) -> List[Difference]:
        return list(self._differences)  # defensive copy
