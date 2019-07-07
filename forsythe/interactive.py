from queue import Queue
from pynput import keyboard


def interactive_process(commands):
    q = Queue()

    def on_key(key):
        if key == keyboard.Key.esc:
            q.put('exit')
            return False

        command = commands.get(key)
        if command:
            q.put(command)
            return False

    while True:
        with keyboard.Listener(on_release=on_key) as listener:
            listener.join()
        command = q.get()
        if command == 'exit':
            break

        yield command
