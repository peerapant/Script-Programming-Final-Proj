import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class RockSpecFolderWatcher(FileSystemEventHandler):
    def __init__(self, pipeline, dry_run: bool = False):
        self.pipeline = pipeline
        self.dry_run = dry_run
        self.last_triggered = 0.0

    def on_created(self, event):
        if event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_triggered > 3:
            if event.src_path.lower().endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg')):
                print(f"\n[WATCHER DETECTED] พบไฟล์ใหม่: {event.src_path}")
                time.sleep(1)
                self.pipeline.run(dry_run=self.dry_run)
                self.last_triggered = time.time()


def start_folder_watcher(watch_dir: str, pipeline):
    event_handler = RockSpecFolderWatcher(pipeline, dry_run=False)
    observer = Observer()
    observer.schedule(event_handler, path=watch_dir, recursive=True)
    observer.start()
    print(f"🚀 [Folder Watcher Started] กำลังเฝ้าระวังโฟลเดอร์: {watch_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 หยุดการทำงานของ Folder Watcher")
    observer.join()