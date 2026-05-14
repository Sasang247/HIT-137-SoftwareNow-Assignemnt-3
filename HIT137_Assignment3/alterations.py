"""
alterations.py
--------------
Image-alteration strategy classes used to introduce hidden differences into
the cloned image.

OOP techniques demonstrated:
    * Inheritance:  every concrete alteration extends :class:`Alteration`.
    * Polymorphism: :class:`ImageProcessor` holds a list of *base-class
      references* and invokes ``apply()`` without caring which subclass it
      is dealing with - each subclass overrides ``apply`` with its own
      OpenCV implementation.
    * Encapsulation: subclasses keep their tuning parameters as private
      class attributes (``_HUE_MIN`` etc.).
    * Multiple inheritance (mix-in): the :class:`LoggableMixin` adds a
      lightweight logging helper to every alteration without altering the
      base class.
    * Abstract methods via :mod:`abc` to forbid instantiating the bare
      base class.

All pixel manipulation is performed with OpenCV (``cv2``) as required by
the assignment specification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import cv2
import numpy as np


# ---------------------------------------------------------------------- #
# Mix-in providing a tiny logging helper (multiple inheritance).          #
# ---------------------------------------------------------------------- #
class LoggableMixin:
    """Adds a ``log`` method that can be silenced globally.

    Demonstrates the *mix-in* pattern: combine this class with any other
    class via multiple inheritance to gain logging without subclassing.
    """

    VERBOSE: ClassVar[bool] = False

    def log(self, message: str) -> None:
        if self.VERBOSE:
            print(f"[{self.__class__.__name__}] {message}")


# ---------------------------------------------------------------------- #
# Abstract base class.                                                   #
# ---------------------------------------------------------------------- #
class Alteration(LoggableMixin, ABC):
    """Abstract base class for every kind of image alteration.

    Subclasses must override :meth:`apply`.  The class name acts as the
    ``name`` attribute (e.g. ``"BlurAlteration"``).
    """

    #: Human-readable name shown in the status bar.
    display_name: ClassVar[str] = "Alteration"

    @abstractmethod
    def apply(self, image: np.ndarray, x: int, y: int,
              w: int, h: int) -> None:
        """Mutate ``image`` in-place inside the rectangle ``(x, y, w, h)``."""
        raise NotImplementedError

    # Polymorphic helper: subclasses don't override this.
    def __call__(self, image: np.ndarray, x: int, y: int,
                 w: int, h: int) -> None:
        self.log(f"applying to ({x},{y},{w},{h})")
        self.apply(image, x, y, w, h)


# ---------------------------------------------------------------------- #
# Concrete alterations.                                                  #
# ---------------------------------------------------------------------- #
class BlurAlteration(Alteration):
    """Apply a strong Gaussian blur inside the region."""

    display_name = "blur"

    def apply(self, image: np.ndarray, x: int, y: int,
              w: int, h: int) -> None:
        roi = image[y:y + h, x:x + w]
        # Kernel must be odd; scale with region size for a subtle effect.
        k = max(7, (min(w, h) // 3) | 1)
        image[y:y + h, x:x + w] = cv2.GaussianBlur(roi, (k, k), 0)


class ColourShiftAlteration(Alteration):
    """Shift hue + saturation inside the region using HSV space.

    Matches the example given in the assignment brief
    ("rectangular region whose colour properties are shifted").
    """

    display_name = "colour shift"

    def apply(self, image: np.ndarray, x: int, y: int,
              w: int, h: int) -> None:
        roi = image[y:y + h, x:x + w]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV).astype(np.int16)
        # Hue is 0..179 in OpenCV.
        hue_delta = int(np.random.choice([-50, -35, 35, 50]))
        sat_delta = int(np.random.choice([-40, -25, 25, 40]))
        hsv[..., 0] = (hsv[..., 0] + hue_delta) % 180
        hsv[..., 1] = np.clip(hsv[..., 1] + sat_delta, 0, 255)
        image[y:y + h, x:x + w] = cv2.cvtColor(
            hsv.astype(np.uint8), cv2.COLOR_HSV2BGR
        )


class BrightnessAlteration(Alteration):
    """Brighten or darken the region with a uniform additive offset."""

    display_name = "brightness"

    def apply(self, image: np.ndarray, x: int, y: int,
              w: int, h: int) -> None:
        roi = image[y:y + h, x:x + w]
        beta = float(np.random.choice([-55, -40, 40, 55]))
        image[y:y + h, x:x + w] = cv2.convertScaleAbs(roi, alpha=1.0, beta=beta)


class NoiseAlteration(Alteration):
    """Add Gaussian noise to the region - a subtle texture change."""

    display_name = "noise"

    def apply(self, image: np.ndarray, x: int, y: int,
              w: int, h: int) -> None:
        roi = image[y:y + h, x:x + w].astype(np.int16)
        noise = np.random.normal(0, 28, roi.shape).astype(np.int16)
        image[y:y + h, x:x + w] = np.clip(roi + noise, 0, 255).astype(np.uint8)


class MirrorAlteration(Alteration):
    """Horizontally flip the contents of the region.

    Uses :func:`cv2.flip`, demonstrating yet another OpenCV primitive.
    """

    display_name = "mirror"

    def apply(self, image: np.ndarray, x: int, y: int,
              w: int, h: int) -> None:
        roi = image[y:y + h, x:x + w]
        image[y:y + h, x:x + w] = cv2.flip(roi, 1)


# Convenience: list of all alteration types used by ``ImageProcessor``.
ALL_ALTERATIONS = [
    BlurAlteration,
    ColourShiftAlteration,
    BrightnessAlteration,
    NoiseAlteration,
    MirrorAlteration,
]
