#!/bin/sh
# title=PICO-8 Renamer
# icon=assets/icon.png
# description=Safely rename PICO-8 carts using shrinko8
SCRIPT_DIR=$(dirname "$0")

if [ -f "/mnt/SDCARD/spruce/scripts/helperFunctions.sh" ]; then
    . /mnt/SDCARD/spruce/scripts/helperFunctions.sh
    PYTHON_EXEC=$(get_python_path)
    
    if [ "$PLATFORM" = "Flip" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/App/PyUI/dll"
    elif [ "$PLATFORM" = "A30" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/spruce/a30/sdl2"
    elif [ "$PLATFORM" = "Brick" ] || [ "$PLATFORM" = "SmartPro" ] || [ "$PLATFORM" = "SmartProS" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/spruce/brick/sdl2"
    elif [ "$PLATFORM" = "MiyooMini" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/spruce/miyoomini/lib"
    elif [ "$PLATFORM" = "Pixel2" ]; then
        export PYSDL2_DLL_PATH="/usr/lib"
    else
        export PYSDL2_DLL_PATH="/usr/lib/aarch64-linux-gnu/"
        export LD_LIBRARY_PATH="/usr/lib32:/usr/lib:/mnt/vendor/lib:$LD_LIBRARY_PATH"
    fi
else
    PYTHON_EXEC="python3"
fi

export PYTHONPATH="$SCRIPT_DIR/libs:$PYTHONPATH"

cd "$SCRIPT_DIR"

"$PYTHON_EXEC" main.py > "$SCRIPT_DIR/device_runtime.log" 2>&1
