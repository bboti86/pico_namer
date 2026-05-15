import os
import re
import sys
import queue
import string

# Import shrinko8 safely
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs/shrinko8'))
from pico_cart import read_cart
from logger import setup_logger

logger = setup_logger("pico_backend")

def sanitize_filename(name):
    # Remove invalid characters for FAT32
    name = re.sub(r'[\\/:*?"<>|]', ' ', name)
    # Remove non-ascii or weird characters that might be in PICO-8 titles
    name = "".join(c for c in name if c.isprintable() or c.isspace())
    
    # Strip leading/trailing borders/decorations
    name = name.strip('-=~_#*+ ')
    
    # Collapse multiple spaces and strip
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Capitalize like a book title
    name = string.capwords(name)
    return name

def fallback_title_from_filename(filename):
    base = filename
    for ext in ['.p8.png', '.p8']:
        if base.lower().endswith(ext):
            base = base[:-len(ext)]
            break
            
    # Check if the filename is just numbers (BBS IDs like 56656)
    if base.isdigit():
        return "" # A digit-only title is useless, just skip
        
    # Replace dashes and underscores with spaces
    base = base.replace('-', ' ').replace('_', ' ')
    
    # Remove common revision suffixes like "v1", "1 0" at the end
    base = re.sub(r'\s+v?\d+([ \.]\d+)*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'\s+\d+$', '', base)
    
    return sanitize_filename(base)

def get_unique_path(directory, filename, ext):
    base_path = os.path.join(directory, f"{filename}{ext}")
    if not os.path.exists(base_path):
        return base_path
    
    counter = 1
    while True:
        new_path = os.path.join(directory, f"{filename} ({counter}){ext}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def run_renamer(target_dirs, progress_queue, dry_run=False, cancel_event=None):
    files_to_process = []
    
    # Traverse directories
    for tdir in target_dirs:
        if not os.path.exists(tdir):
            continue
        for root, _, files in os.walk(tdir):
            for file in files:
                if file.lower().endswith('.p8') or file.lower().endswith('.p8.png'):
                    files_to_process.append(os.path.join(root, file))
                    
    total = len(files_to_process)
    logger.info(f"Directory scan complete. Found {total} PICO-8 files to process.")
    progress_queue.put({"type": "START", "total": total})
    
    if total == 0:
        progress_queue.put({"type": "COMPLETE", "success": 0, "failures": []})
        return

    success_count = 0
    failures = []

    for index, filepath in enumerate(files_to_process):
        if cancel_event and cancel_event.is_set():
            logger.info("Renamer cancelled by user.")
            return

        filename = os.path.basename(filepath)
        dirname = os.path.dirname(filepath)
        ext = '.p8.png' if filename.lower().endswith('.p8.png') else '.p8'
        
        try:
            # Tell UI we are starting this file
            progress_queue.put({
                "type": "UPDATE",
                "index": index + 1,
                "total": total,
                "msg": f"Parsing: {filename}"
            })
            
            cart = read_cart(filepath)
            raw_title = cart.title
            clean_title = ""
            
            if raw_title and raw_title.strip() != "":
                # Get the first line of the title if multiline
                first_line = raw_title.split('\n')[0].strip()
                clean_title = sanitize_filename(first_line)
                
            bad_titles = ['todo', 'init', 'game', 'main', 'app', 'globals', 'overall', 'title']
            if not clean_title or clean_title.lower() in bad_titles:
                fallback = fallback_title_from_filename(filename)
                if fallback:
                    clean_title = fallback
            
            if not clean_title:
                progress_queue.put({
                    "type": "UPDATE",
                    "index": index + 1,
                    "total": total,
                    "msg": f"Skipped (No Title Found): {filename}"
                })
                logger.info(f"Skipped (No Title Found): '{filename}'")
                failures.append(f"{filename} - No valid title found")
                continue
                
            # Keep original if it already matches
            if filename == f"{clean_title}{ext}":
                progress_queue.put({
                    "type": "UPDATE",
                    "index": index + 1,
                    "total": total,
                    "msg": f"Skipped (Already Named): {filename}"
                })
                success_count += 1
                continue
                
            new_filepath = get_unique_path(dirname, clean_title, ext)
            new_filename = os.path.basename(new_filepath)
            
            progress_queue.put({
                "type": "UPDATE",
                "index": index + 1,
                "total": total,
                "msg": f"Renaming: {filename} -> {new_filename}"
            })
            
            if not dry_run:
                os.rename(filepath, new_filepath)
                logger.info(f"Renamed: '{filename}' -> '{new_filename}'")
            else:
                logger.info(f"Dry Run Renamed: '{filename}' -> '{new_filename}'")
                
            success_count += 1
            
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Failed to process {filename}: {err_msg}")
            failures.append(f"{filename} - {err_msg}")
            progress_queue.put({
                "type": "UPDATE",
                "index": index + 1,
                "total": total,
                "msg": f"Failed: {filename} ({err_msg})"
            })

    logger.info(f"Renamer completed. Successes: {success_count}, Failures: {len(failures)}")
    progress_queue.put({
        "type": "COMPLETE",
        "success": success_count,
        "failures": failures
    })
