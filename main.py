import sys
import os
import time
import queue
import threading

import sdl2
import sdl2.ext
import sdl2.sdlttf

# Adjust python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

import input as input_handlers
from ui_utils import draw_panel, render_text, render_text_shadow, draw_progress_bar
from pico_backend import run_renamer
from logger import setup_logger

logger = setup_logger("main")

# Constants
WIDTH, HEIGHT = 640, 480
FPS = 60

STATE_DASHBOARD = 0
STATE_PROCESSING = 1
STATE_SUMMARY = 2

# Global state
app_state = STATE_DASHBOARD
target_dirs = [
    "/media/sdcard0/Roms/PICO8",
    "/media/sdcard1/Roms/PICO8"
]
worker_thread = None
progress_queue = queue.Queue()
cancel_event = threading.Event()

# Processing state
current_progress = 0
total_files = 0
log_messages = []

# Summary state
success_count = 0
failure_messages = []

def change_state(new_state):
    global app_state, current_progress, total_files, log_messages, success_count, failure_messages
    app_state = new_state
    if new_state == STATE_DASHBOARD:
        current_progress = 0
        total_files = 0
        log_messages = []
        success_count = 0
        failure_messages = []
        while not progress_queue.empty():
            try:
                progress_queue.get_nowait()
            except queue.Empty:
                break

def start_processing(dry_run):
    global worker_thread, log_messages
    log_messages = ["Starting " + ("Dry Run..." if dry_run else "Renamer...")]
    cancel_event.clear()
    change_state(STATE_PROCESSING)
    worker_thread = threading.Thread(target=run_renamer, args=(target_dirs, progress_queue, dry_run, cancel_event), daemon=True)
    worker_thread.start()

def main():
    global app_state, current_progress, total_files, log_messages, success_count, failure_messages

    sdl2.ext.init()
    sdl2.sdlttf.TTF_Init()
    input_handlers.init_joysticks()

    window = sdl2.ext.Window("PICO-8 Renamer", size=(WIDTH, HEIGHT), flags=sdl2.SDL_WINDOW_SHOWN)
    renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC)
    renderer.blendmode = sdl2.SDL_BLENDMODE_BLEND

    font_path = os.path.join(os.path.dirname(__file__), "assets", "font.ttf")
    
    # Try to load font. If missing, fall back to default or error out gracefully
    if not os.path.exists(font_path):
        # We will use a dummy/fallback font path if we can find one on the system, else it will crash TTF_OpenFont
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" 
    
    try:
        font_large = sdl2.sdlttf.TTF_OpenFont(font_path.encode('utf-8'), 32)
        font_medium = sdl2.sdlttf.TTF_OpenFont(font_path.encode('utf-8'), 24)
        font_small = sdl2.sdlttf.TTF_OpenFont(font_path.encode('utf-8'), 16)
    except Exception as e:
        logger.error(f"Failed to load fonts: {e}")
        return

    logger.info("Application starting up.")
    running = True

    while running:
        # Event handling
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            
            action = input_handlers.map_event(event)
            if action:
                if app_state == STATE_DASHBOARD:
                    if action == input_handlers.ACCEPT or action == input_handlers.START:
                        logger.info("User requested Start Processing (Execution Mode)")
                        start_processing(dry_run=False)
                    elif action == "X" or action == input_handlers.SELECT: # Map X/Select to Dry Run
                        logger.info("User requested Start Processing (Dry Run)")
                        start_processing(dry_run=True)
                    elif action == input_handlers.CANCEL:
                        logger.info("User requested Exit from Dashboard")
                        running = False
                        
                elif app_state == STATE_PROCESSING:
                    if action == input_handlers.CANCEL:
                        logger.info("User requested Cancel during Processing")
                        cancel_event.set()
                        change_state(STATE_DASHBOARD)
                        
                elif app_state == STATE_SUMMARY:
                    if action == input_handlers.CANCEL or action == input_handlers.ACCEPT:
                        logger.info("User requested return to Dashboard")
                        change_state(STATE_DASHBOARD)

        # Queue handling in Processing state
        if app_state == STATE_PROCESSING:
            while not progress_queue.empty():
                try:
                    msg = progress_queue.get_nowait()
                    if msg['type'] == 'START':
                        total_files = msg['total']
                    elif msg['type'] == 'UPDATE':
                        current_progress = msg['index']
                        log_messages.append(msg['msg'])
                        # Keep last 10 messages
                        if len(log_messages) > 10:
                            log_messages.pop(0)
                    elif msg['type'] == 'COMPLETE':
                        success_count = msg['success']
                        failure_messages = msg['failures']
                        change_state(STATE_SUMMARY)
                except queue.Empty:
                    break

        # Rendering
        renderer.clear(sdl2.ext.Color(10, 10, 15))

        if app_state == STATE_DASHBOARD:
            draw_panel(renderer, 20, 20, WIDTH - 40, HEIGHT - 80)
            render_text_shadow(renderer, font_large, "PICO-8 ROM Renamer", WIDTH//2, 40, (255, 200, 0), center=True)
            
            y_pos = 120
            render_text(renderer, font_medium, "Target Directories:", 40, y_pos, (200, 200, 200))
            for tdir in target_dirs:
                y_pos += 30
                color = (100, 255, 100) if os.path.exists(tdir) else (255, 100, 100)
                render_text(renderer, font_small, tdir, 60, y_pos, color)
            
            render_text(renderer, font_medium, "This utility will parse PICO-8 titles", 40, y_pos + 60, (200, 200, 200))
            render_text(renderer, font_medium, "and safely rename files so they look nicer.", 40, y_pos + 90, (200, 200, 200))

            # Footer
            render_text(renderer, font_small, "[A/START]: Execute  |  [X/SELECT]: Dry Run  |  [B]: Exit", WIDTH//2, HEIGHT - 30, (150, 150, 150), center=True)

        elif app_state == STATE_PROCESSING:
            draw_panel(renderer, 20, 20, WIDTH - 40, HEIGHT - 80)
            render_text_shadow(renderer, font_large, "Processing...", WIDTH//2, 40, (0, 200, 255), center=True)
            
            prog_ratio = current_progress / max(1, total_files)
            draw_progress_bar(renderer, 40, 120, WIDTH - 80, 30, prog_ratio)
            render_text(renderer, font_small, f"{current_progress} / {total_files}", WIDTH//2, 126, (255, 255, 255), center=True)
            
            y_pos = 180
            for msg in log_messages[-8:]:
                render_text(renderer, font_small, msg, 40, y_pos, (200, 200, 200))
                y_pos += 25

            # Footer
            render_text(renderer, font_small, "[B]: Cancel & Return to Dashboard", WIDTH//2, HEIGHT - 30, (150, 150, 150), center=True)

        elif app_state == STATE_SUMMARY:
            draw_panel(renderer, 20, 20, WIDTH - 40, HEIGHT - 80)
            render_text_shadow(renderer, font_large, "Operation Complete", WIDTH//2, 40, (0, 255, 100), center=True)
            
            render_text(renderer, font_medium, f"Total Scanned: {total_files}", 40, 120, (200, 200, 200))
            render_text(renderer, font_medium, f"Successful Renames: {success_count}", 40, 160, (100, 255, 100))
            
            if failure_messages:
                render_text(renderer, font_medium, "Failures/Skipped:", 40, 200, (255, 100, 100))
                y_pos = 230
                for msg in failure_messages[:6]:
                    # truncate if too long
                    msg = msg[:70] + "..." if len(msg) > 70 else msg
                    render_text(renderer, font_small, msg, 60, y_pos, (255, 150, 150))
                    y_pos += 25
                if len(failure_messages) > 6:
                    render_text(renderer, font_small, f"... and {len(failure_messages) - 6} more.", 60, y_pos, (255, 150, 150))
            else:
                render_text(renderer, font_medium, "No failures!", 40, 220, (100, 255, 100))

            # Footer
            render_text(renderer, font_small, "[B]: Return to Dashboard", WIDTH//2, HEIGHT - 30, (150, 150, 150), center=True)

        renderer.present()
        sdl2.SDL_Delay(16)

    logger.info("Application exiting.")
    sdl2.sdlttf.TTF_CloseFont(font_large)
    sdl2.sdlttf.TTF_CloseFont(font_medium)
    sdl2.sdlttf.TTF_CloseFont(font_small)
    sdl2.sdlttf.TTF_Quit()
    sdl2.ext.quit()

if __name__ == "__main__":
    main()
