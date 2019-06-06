import time
import win32gui
import win32con
import win32api
import win32com.client

from forsythe.eos.device import device_is_connected
from forsythe.eos.process import run_eos_utility

__splash_title__ = 'EOS Utility 3'
__control_title__ = ' EOS Rebel T6'
__liveview_title__ = 'Remote Live View window'


def find_eos_windows():
    def handler(hwnd, out_result):
        title = win32gui.GetWindowText(hwnd)
        if title == __splash_title__:
            out_result['splash'] = hwnd
        elif title == __control_title__:
            out_result['control'] = hwnd
        elif title == __liveview_title__:
            out_result['liveview'] = hwnd
    result = {x: None for x in ('splash', 'control', 'liveview')}
    win32gui.EnumWindows(handler, result)
    return result['splash'], result['control'], result['liveview']


def wait_for_window(title, timeout=5.0, interval=0.25):

    def handler(hwnd, out_result):
        if win32gui.GetWindowText(hwnd) == title:
            out_result[0] = hwnd

    print("Waiting for window '%s' to open..." % title)

    elapsed = 0.0
    while elapsed < timeout:
        result = [None]
        win32gui.EnumWindows(handler, result)
        if result[0]:
            return result[0]
        time.sleep(interval)
        elapsed += interval

    raise RuntimeError("Failed to find window '%s' after %0.2f seconds" % (title, timeout))


def wait_for_close(title, timeout=5.0, interval=0.25):

    def handler(hwnd, out_result):
        if win32gui.GetWindowText(hwnd) == title:
            out_result[0] = hwnd

    elapsed = 0.0
    while elapsed < timeout:
        result = [None]
        win32gui.EnumWindows(handler, result)
        if not result[0]:
            return
        time.sleep(interval)
        elapsed += interval

    raise RuntimeError("Window '%s' failed to close after %0.2f seconds" % (title, timeout))


def click(hwnd, x, y):
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.05)

    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (x, y))
    win32api.SetCursorPos((screen_x, screen_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
    time.sleep(0.05)


def activate_liveview():
    splash, control, liveview = find_eos_windows()
    if not liveview:
        if not control:
            if not splash:
                run_eos_utility()
                splash = wait_for_window(__splash_title__)
                assert splash

            click(splash, 100, 200)
            control = wait_for_window(__control_title__)
            assert control

        click(control, 100, 500)
        liveview = wait_for_window(__liveview_title__, timeout=10.0)
        assert liveview

    win32gui.ShowWindow(liveview, win32con.SW_SHOW)
    win32gui.SetForegroundWindow(liveview)


def close_eos_windows():
    splash, control, liveview = find_eos_windows()
    if liveview:
        win32gui.PostMessage(liveview, win32con.WM_CLOSE, 0, 0)
        wait_for_close(__liveview_title__)
        splash, control, liveview = find_eos_windows()
        assert not liveview

    if control:
        win32gui.PostMessage(control, win32con.WM_CLOSE, 0, 0)
        wait_for_close(__control_title__)
        splash, control, liveview = find_eos_windows()
        assert not control and not liveview

    if splash:
        win32gui.PostMessage(splash, win32con.WM_CLOSE, 0, 0)
        wait_for_close(__splash_title__)
        splash, control, liveview = find_eos_windows()
        assert not splash and not control and not liveview


def capture_liveview_photo():
    activate_liveview()
    time.sleep(0.1)
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(' ')
