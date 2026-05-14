"""
app.py
------
Tkinter GUI for the Spot-the-Difference game.

This module defines :class:`SpotDifferenceApp` which **inherits from**
:class:`tkinter.Tk` (inheritance) and composes an :class:`ImageProcessor`
and a :class:`GameState`.  All click handling, drawing of red / blue
circles, status updates and dialog popups live here.

OOP techniques demonstrated in this file:
    * Inheritance from ``tk.Tk`` (and from a small ``StyledWidget``
      helper) plus polymorphism via the ``Alteration`` hierarchy held by
      ``ImageProcessor``.
    * Encapsulation - the GUI never touches the internals of
      ``GameState`` or ``ImageProcessor`` except via their public API.
    * Class interaction between the four major classes
      (``ImageProcessor``, ``GameState``, ``Difference``,
      ``SpotDifferenceApp``).
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Tuple

import cv2
from PIL import Image, ImageTk

from difference import Difference
from game_state import GameState
from image_processor import ImageProcessor


# ---------------------------------------------------------------------- #
# A tiny styling helper - shows another piece of inheritance and keeps   #
# the colours consistent across the UI.                                  #
# ---------------------------------------------------------------------- #
class Theme:
    """Centralised colour / font palette (Catppuccin-Mocha inspired)."""

    BG = "#1e1e2e"
    BG_PANEL = "#313244"
    BG_CANVAS = "#11111b"
    BORDER = "#45475a"
    FG = "#cdd6f4"
    ACCENT_PRIMARY = "#89b4fa"   # Load button
    ACCENT_REVEAL = "#f9e2af"    # Reveal button
    ACCENT_OK = "#a6e3a1"        # Remaining (green)
    ACCENT_ERR = "#f38ba8"       # Mistakes  (red)
    ACCENT_SCORE = "#cba6f7"     # Total found (purple)
    FONT_TITLE = ("Segoe UI", 13, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_STAT = ("Segoe UI", 12, "bold")


# ---------------------------------------------------------------------- #
# Main application class.                                                #
# ---------------------------------------------------------------------- #
class SpotDifferenceApp(tk.Tk):
    """Top-level Tkinter window for the game."""

    #: Pixel-distance tolerance for "close enough" clicks.
    CLICK_TOLERANCE: int = 22

    #: Maximum size (w, h) any loaded image will be scaled to fit inside.
    MAX_IMAGE_SIZE: Tuple[int, int] = (720, 620)

    SUPPORTED_FORMATS = [
        ("Image files", "*.jpg *.jpeg *.png *.bmp"),
        ("JPEG", "*.jpg *.jpeg"),
        ("PNG", "*.png"),
        ("Bitmap", "*.bmp"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.title("HIT137 - Spot the Difference")
        self.configure(bg=Theme.BG)
        self.geometry("1640x820")
        self.minsize(1200, 720)

        # --- Composition (class interaction) ----------------------------
        self._processor = ImageProcessor(max_size=self.MAX_IMAGE_SIZE)
        self._state = GameState()

        # Keep strong references so the PhotoImages don't get GC'd.
        self._left_photo: ImageTk.PhotoImage | None = None
        self._right_photo: ImageTk.PhotoImage | None = None

        self._build_widgets()
        self._update_status_labels()

    # ================================================================== #
    # Widget construction.                                                #
    # ================================================================== #
    def _build_widgets(self) -> None:
        # ---- Top toolbar ------------------------------------------------
        toolbar = tk.Frame(self, bg=Theme.BG_PANEL, pady=10)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="HIT137  -  Spot the Difference",
                 font=Theme.FONT_TITLE, fg=Theme.FG,
                 bg=Theme.BG_PANEL, padx=14).pack(side="left")

        tk.Button(toolbar, text="Load Image",
                  command=self._on_load, font=Theme.FONT_BODY,
                  bg=Theme.ACCENT_PRIMARY, fg="black",
                  activebackground="#74c7ec", relief="flat",
                  padx=16, pady=4, cursor="hand2"
                  ).pack(side="left", padx=(20, 6))

        tk.Button(toolbar, text="Reveal Unfound",
                  command=self._on_reveal, font=Theme.FONT_BODY,
                  bg=Theme.ACCENT_REVEAL, fg="black",
                  activebackground="#fab387", relief="flat",
                  padx=16, pady=4, cursor="hand2"
                  ).pack(side="left", padx=6)

        # ---- Live counters (StringVars are bound to Labels) ------------
        self._remaining_var = tk.StringVar(value="Remaining: -")
        self._mistakes_var = tk.StringVar(value="Mistakes: 0 / 3")
        self._score_var = tk.StringVar(value="Total Found: 0")

        tk.Label(toolbar, textvariable=self._remaining_var,
                 font=Theme.FONT_STAT, fg=Theme.ACCENT_OK,
                 bg=Theme.BG_PANEL, padx=24).pack(side="left")
        tk.Label(toolbar, textvariable=self._mistakes_var,
                 font=Theme.FONT_STAT, fg=Theme.ACCENT_ERR,
                 bg=Theme.BG_PANEL, padx=24).pack(side="left")
        tk.Label(toolbar, textvariable=self._score_var,
                 font=Theme.FONT_STAT, fg=Theme.ACCENT_SCORE,
                 bg=Theme.BG_PANEL, padx=24).pack(side="left")

        # ---- Status bar -------------------------------------------------
        self._status_var = tk.StringVar(
            value="Load a JPG, PNG, or BMP image to begin."
        )
        tk.Label(self, textvariable=self._status_var,
                 font=Theme.FONT_BODY, fg=Theme.FG, bg=Theme.BG,
                 anchor="w", padx=16, pady=6
                 ).pack(fill="x")

        # ---- Twin canvases ---------------------------------------------
        canvases = tk.Frame(self, bg=Theme.BG)
        canvases.pack(expand=True, fill="both", padx=16, pady=10)

        self._left_canvas = self._make_image_panel(
            canvases, "Original  (reference only)", clickable=False
        )
        self._right_canvas = self._make_image_panel(
            canvases, "Modified  (click here to find differences)",
            clickable=True
        )
        # Bind the click only on the modified canvas, as required.
        self._right_canvas.bind("<Button-1>", self._on_click)

    def _make_image_panel(self, parent: tk.Widget, label: str,
                          clickable: bool) -> tk.Canvas:
        """Create a captioned canvas inside ``parent``.  Returns the canvas."""
        frame = tk.Frame(parent, bg=Theme.BG)
        frame.pack(side="left", expand=True, fill="both", padx=10)

        tk.Label(frame, text=label, font=Theme.FONT_TITLE,
                 fg=Theme.FG, bg=Theme.BG, pady=6).pack()

        canvas = tk.Canvas(
            frame, bg=Theme.BG_CANVAS, highlightthickness=2,
            highlightbackground=Theme.BORDER,
            width=self.MAX_IMAGE_SIZE[0],
            height=self.MAX_IMAGE_SIZE[1],
            cursor="crosshair" if clickable else "arrow",
        )
        canvas.pack(expand=True, fill="both")
        return canvas

    # ================================================================== #
    # Event handlers.                                                    #
    # ================================================================== #
    def _on_load(self) -> None:
        """Open a file dialog, load and process the chosen image."""
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=self.SUPPORTED_FORMATS,
        )
        if not path:
            return

        try:
            self._processor.load_image(path)
            _, diffs = self._processor.generate_differences()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Could not load image", str(exc))
            return

        self._state.reset_for_new_image(diffs)
        self._display_images()
        self._update_status_labels()
        self._status_var.set(
            f"Loaded '{os.path.basename(path)}'.  "
            f"Find 5 hidden differences by clicking the right image."
        )

    def _on_click(self, event: tk.Event) -> None:
        """Handle a player click on the modified-image canvas."""
        if self._state.locked:
            self._status_var.set(
                "Round locked - load a new image to play again."
            )
            return
        if not self._processor.differences:
            self._status_var.set("Load an image first.")
            return

        hit = self._state.register_click(
            event.x, event.y, tolerance=self.CLICK_TOLERANCE
        )
        if hit is not None:
            self._draw_circle(hit, colour="#f38ba8", tag="found")  # red
            self._status_var.set(
                f"Correct!  Found a '{hit.alteration_type}' difference."
            )
            if self._state.all_found:
                self._update_status_labels()
                messagebox.showinfo(
                    "Round complete",
                    "Excellent - you found all 5 differences!\n\n"
                    "Load another image to keep playing."
                )
        else:
            self._status_var.set(
                f"Miss!  ({self._state.mistakes}/3 mistakes used)"
            )
            if self._state.locked:
                found = len(
                    [d for d in self._processor.differences if d.found]
                )
                messagebox.showwarning(
                    "Too many mistakes",
                    f"You've used all 3 mistakes for this image.\n\n"
                    f"Differences found: {found} / 5\n\n"
                    f"Load a new image to restart."
                )

        self._update_status_labels()

    def _on_reveal(self) -> None:
        """Mark all unfound differences with a blue circle on both images."""
        if not self._processor.differences:
            self._status_var.set("Load an image first.")
            return

        unfound = self._state.reveal_unfound()
        for d in unfound:
            self._draw_circle(d, colour="#74c7ec", tag="reveal")  # blue

        self._update_status_labels()
        if unfound:
            self._status_var.set(
                f"Revealed {len(unfound)} unfound difference(s) in blue. "
                "Load a new image to continue."
            )
        else:
            self._status_var.set(
                "All differences were already found!"
            )

    # ================================================================== #
    # Drawing helpers.                                                   #
    # ================================================================== #
    def _display_images(self) -> None:
        """Render the original and modified images into the two canvases."""
        original = self._processor.original
        modified = self._processor.modified
        if original is None or modified is None:
            return

        # OpenCV ships BGR; PIL / Tkinter expect RGB.
        self._left_photo = self._cv_to_photo(original)
        self._right_photo = self._cv_to_photo(modified)

        h, w = original.shape[:2]
        for canvas, photo in ((self._left_canvas, self._left_photo),
                              (self._right_canvas, self._right_photo)):
            canvas.delete("all")
            canvas.config(width=w, height=h)
            canvas.create_image(0, 0, anchor="nw", image=photo, tags="img")

    @staticmethod
    def _cv_to_photo(bgr_image) -> ImageTk.PhotoImage:
        """Convert a BGR OpenCV image to a Tkinter ``PhotoImage``."""
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def _draw_circle(self, diff: Difference, colour: str, tag: str) -> None:
        """Draw a coloured circle around ``diff`` on **both** canvases."""
        cx, cy = diff.center
        r = diff.radius
        for canvas in (self._left_canvas, self._right_canvas):
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=colour, width=3, tags=tag,
            )

    # ================================================================== #
    # Status-bar refresh.                                                #
    # ================================================================== #
    def _update_status_labels(self) -> None:
        diffs = self._processor.differences
        if diffs:
            self._remaining_var.set(f"Remaining: {self._state.remaining}")
        else:
            self._remaining_var.set("Remaining: -")
        self._mistakes_var.set(f"Mistakes: {self._state.mistakes} / 3")
        self._score_var.set(f"Total Found: {self._state.total_found}")
