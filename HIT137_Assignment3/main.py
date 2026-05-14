"""
main.py
-------
Entry point for the HIT137 Group Assignment 3 Spot-the-Difference game.

Run:
    python main.py

Dependencies (see ``requirements.txt``):
    opencv-python  - all image manipulation
    Pillow         - bridge between OpenCV and Tkinter PhotoImage
    numpy          - OpenCV's array backing store

Tkinter ships with the Python standard library on the major platforms.
"""

from __future__ import annotations

from app import SpotDifferenceApp


def main() -> None:
    app = SpotDifferenceApp()
    app.mainloop()


if __name__ == "__main__":
    main()
