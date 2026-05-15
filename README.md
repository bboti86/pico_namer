# PICO-8 ROM Renamer for Spruce OS

A beautiful, native utility for **Spruce OS** (Miyoo Flip, Miyoo Mini Plus, etc.) that automatically renames PICO-8 carts using their internal metadata.

## 🚀 The Goal
When you download PICO-8 carts from the BBS, they often have names like `56656.p8.png` or `bunnysurvivor-9.p8.png`. This utility parses the cart's Lua code to find the actual title comment and renames the file to a clean, human-readable format (e.g., `Watermelon Game.p8.png`).

## ✨ Features
- **Smart Metadata Extraction**: Uses `shrinko8` to safely parse PICO-8 carts (`.p8` and `.p8.png`).
- **Clean Titles**: Automatically strips out ASCII art borders (`-- title --`), decorations, and invalid filename characters.
- **Smart Fallbacks**: If a cart is missing a title comment or contains generic code words (like `init` or `main`), the app automatically generates a clean title from the original filename.
- **Dry Run Mode**: Preview all changes in a log before committing to any file renames.
- **Duplicate Protection**: Automatically handles naming collisions by appending unique counters.
- **Native UI**: A sleek PySDL2-based interface designed for handheld screens.

## 🛠️ How to Use
1. **Launch**: Open **PICO-8 Renamer** from your Apps menu on Spruce OS.
2. **Dashboard**: The app will show the detected ROM directories.
3. **Dry Run (Recommended)**: Press **[X]** or **[SELECT]** to perform a scan. It will log every proposed change to `device_runtime.log` without modifying your files. In this mode it will also display the list of files that the app was not able to determine a title for.
4. **Rename**: Press **[A]** or **[START]** to execute the renaming process.
5. **Review**: Check the summary screen for success/failure counts.

## 📱 Compatibility
- **Primary Platform**: Tested and verified on the **Miyoo Flip v2**.
- **Spruce OS Support**: Should run on all Spruce-compatible devices (A30, Mini Plus, etc.) as it uses the standard Spruce Python environment.

## 🏗️ Development & Deployment
The project includes an `auto_push.py` script for developers to quickly sync changes to a device over SSH.
```bash
# Requires IP 10.0.2.1 and password 'happygaming' (standard Spruce defaults)
./auto_push.py
```

## 📜 Credits
- **[shrinko8](https://github.com/thisismypassport/shrinko8)**: Core cart parsing logic.
- **PySDL2**: Powering the handheld user interface.
- **Spruce OS Team**: For the wonderful handheld environment.
