"""Real-time knowledge base: re-index automatically whenever a file is added/edited/removed."""
import threading
from . import config

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # optional dependency
    Observer = None


def start_watcher(on_change):
    if Observer is None:
        print("[watcher] watchdog not installed - live reload disabled")
        return None
    timer = {"t": None}

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            if event.is_directory:
                return
            if timer["t"]:
                timer["t"].cancel()
            timer["t"] = threading.Timer(1.0, on_change)  # debounce bursts of events
            timer["t"].daemon = True
            timer["t"].start()

    obs = Observer()
    obs.schedule(Handler(), str(config.KB_DIR), recursive=True)
    obs.daemon = True
    obs.start()
    print(f"[watcher] watching {config.KB_DIR}")
    return obs
