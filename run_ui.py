import sys
import os
import time
import atexit
import subprocess
import requests
from ui.main_window import RPGTrackerApp

API_URL = "http://127.0.0.1:8000"
api_process: subprocess.Popen | None = None


def stop_api_server():
    """Гарантовано завершує процес Uvicorn та всі його дочірні потоки."""
    global api_process
    if api_process is not None and api_process.poll() is None:
        try:
            if os.name == "nt":
                # На Windows примусово вбиваємо все дерево процесів (/T) за PID
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(api_process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                api_process.terminate()
                api_process.wait(timeout=3)
        except Exception:
            api_process.kill()
        finally:
            api_process = None


# Реєструємо автозакриття при виході з Python-інтерпретатора
atexit.register(stop_api_server)


def wait_for_api(timeout: float = 8.0):
    """Чекає, поки процес FastAPI підніметься."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{API_URL}/dashboard", timeout=1.0)
            if r.status_code == 200:
                return
        except requests.RequestException:
            time.sleep(0.15)


if __name__ == "__main__":
    # CREATE_NO_WINDOW ховає зайві консольні спливання на Windows
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
        ],
        creationflags=creation_flags,
    )

    try:
        wait_for_api()
        app = RPGTrackerApp(api_url=API_URL)

        # Перехоплюємо натискання на хрестик вікна CustomTkinter
        def on_closing():
            app.destroy()
            stop_api_server()

        app.protocol("WM_DELETE_WINDOW", on_closing)
        app.mainloop()
    finally:
        stop_api_server()