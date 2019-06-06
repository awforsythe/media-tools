import time
import win32com.client

__device_name__ = 'Canon EOS Rebel T6'


def device_is_connected():
    wmi = win32com.client.GetObject("winmgmts:")
    for entity in wmi.InstancesOf("Win32_PnPEntity"):
        if entity.Name == __device_name__:
            return True
    return False


def wait_for_device(timeout=60.0, interval=0.25):
    if device_is_connected():
        return

    print("Waiting for '%s' to connect..." % __device_name__)
    elapsed = 0.0
    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval
        if device_is_connected():
            return

    raise RuntimeError("Device did not connect after %0.2f seconds" % timeout)
