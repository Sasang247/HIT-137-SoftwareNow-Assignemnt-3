# HIT137 Group Assignment 3 — Spot the Difference

A Python desktop game that demonstrates Object-Oriented Programming, Tkinter GUI development, and OpenCV image processing. Two nearly identical images are shown side by side. The right-hand image has had **5 hidden differences** programmatically introduced into it; the player clicks on the modified image to locate them.

## Quick Start

```bash
# 1. Install the dependencies (Python 3.10+ recommended)
pip install -r requirements.txt

# 2. Run the game
python main.py
```

Tkinter is part of the Python standard library on Windows and macOS. On most Linux distributions you may also need to install the system package, e.g. `sudo apt install python3-tk`.

## How to Play

1. Click **Load Image** and choose any JPG, PNG, or BMP file.
2. The original is shown on the left; the modified copy is on the right.
3. Click the modified image to find each of the 5 hidden differences. A **red circle** is drawn on both images when you click on a correct spot.
4. You have a maximum of **3 mistakes per image** — a fourth incorrect click is blocked, and a warning dialog appears.
5. Click **Reveal Unfound** at any time to highlight any remaining differences with a **blue circle**.
6. Load a new image at any point to restart with a freshly generated set of 5 differences.

The toolbar continuously shows three counters: how many differences are still unfound in the current image, how many mistakes you have used, and your cumulative score across every image you have played in this session.

## Project Structure

```
.
├── main.py              # Entry point — launches the Tkinter window
├── app.py               # SpotDifferenceApp (inherits tk.Tk) — all GUI logic
├── image_processor.py   # ImageProcessor — file IO, scaling, region generation
├── alterations.py       # Alteration base class + 5 polymorphic subclasses
├── difference.py        # Difference — geometry + state for one hidden region
├── game_state.py        # GameState — score, mistakes, lockout, reveal
├── requirements.txt
└── README.md
```

## OOP Design

The codebase is split across six classes that collaborate via a clean public API. The following OOP principles are all required by the marking rubric — here is where each one lives.

**Encapsulation.** Every class stores its data in private attributes (a leading underscore, with `__slots__` on `Difference` for stricter enforcement) and exposes them through read-only `@property` accessors. For example `GameState.mistakes`, `GameState.locked`, `Difference.bbox`, and `ImageProcessor.original` all return computed values without allowing external mutation.

**Constructors.** Each class declares an `__init__` that fully initialises its instance — `ImageProcessor(max_size=(720, 620))`, `GameState()`, `Difference(x, y, w, h, alteration_type)`, `SpotDifferenceApp()`.

**Methods + Class interaction.** `SpotDifferenceApp` composes an `ImageProcessor` and a `GameState`. When the user clicks **Load Image** it calls `ImageProcessor.load_image(path)` and `ImageProcessor.generate_differences()`, then passes the resulting list of `Difference` objects to `GameState.reset_for_new_image(...)`. Click events call `GameState.register_click(x, y)` which iterates over each `Difference` and calls `difference.contains_point(x, y)`. None of these classes know about each other's internals.

**Inheritance.** `SpotDifferenceApp` inherits from `tkinter.Tk`. Every concrete alteration in `alterations.py` inherits from the abstract `Alteration` base class. The base class itself inherits from `LoggableMixin`, demonstrating *multiple inheritance* (the mix-in pattern).

**Polymorphism.** `ImageProcessor.generate_differences()` picks a random class from `ALL_ALTERATIONS`, instantiates it, and invokes it as a callable. Because every subclass overrides `apply()` (and the base defines `__call__` that dispatches to it), the processor treats `BlurAlteration`, `ColourShiftAlteration`, `BrightnessAlteration`, `NoiseAlteration`, and `MirrorAlteration` identically — the *correct* `apply` implementation runs based on the runtime type.

## Image Processing

Every pixel manipulation is performed with OpenCV (`cv2`), as required by the brief. The five alteration strategies are: Gaussian blur (`cv2.GaussianBlur`), HSV colour shift (`cv2.cvtColor` + manual hue/saturation maths), uniform brightness offset (`cv2.convertScaleAbs`), additive Gaussian noise (NumPy + clipping), and horizontal mirror (`cv2.flip`). Each time an image is loaded the alteration *type* and *position* are chosen at random, and the placement loop guarantees no two regions overlap by using an axis-aligned bounding-box test with a small safety margin. Region size scales with the image so the difference is subtle but findable — never glaringly obvious.

## GUI Features

The Tkinter interface uses two side-by-side `Canvas` widgets, which lets the app draw red and blue circles as overlay shapes without modifying the underlying images. Click detection has a configurable proximity tolerance (`SpotDifferenceApp.CLICK_TOLERANCE`, default 22 px) so the player does not have to click on the exact pixel. The status bar at the top reports the current state ("Loaded my-image.png. Find 5 hidden differences…", "Correct! Found a 'colour shift' difference.", "Miss! (2/3 mistakes used)", etc.) so the player always has clear feedback.

