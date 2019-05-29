import os
import threading
from contextlib import contextmanager

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from forsythe.images.files import list_image_filenames

__xmp_ext__ = '.xmp'


def list_xmp_filenames(images_dir):
    filenames = []
    for filename in os.listdir(images_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext == __xmp_ext__:
            filenames.append(filename)
    return filenames


def delete_xmp_files(images_dir):
    for xmp_filename in list_xmp_filenames(images_dir):
        xmp_filepath = os.path.join(images_dir, xmp_filename)
        os.remove(xmp_filepath)


class XmpWriteEventHandler(FileSystemEventHandler):

    def __init__(self, num_writes_expected):
        self.num_writes_expected = num_writes_expected
        self.num_writes = 0
        self.xmps_seen = set()
        self.lock = threading.Lock()
        self.lock.acquire(blocking=False)

    def wait(self):
        self.lock.acquire(blocking=True)

    def _on_xmp_write(self):
        self.num_writes += 1
        if self.num_writes == self.num_writes_expected:
            self.lock.release()

    def on_any_event(self, event):
        if event.event_type in ('created', 'modified'):
            src_path = event.src_path.lower()
            if os.path.splitext(src_path)[1] == __xmp_ext__ and src_path not in self.xmps_seen:
                self.xmps_seen.add(src_path)
                self._on_xmp_write()


@contextmanager
def wait_for_xmp_writes(images_dir):
    num_images = len(list_image_filenames(images_dir))
    handler = XmpWriteEventHandler(num_images)
    observer = Observer()
    observer.schedule(handler, images_dir)
    observer.start()
    yield
    handler.wait()
    observer.stop()
