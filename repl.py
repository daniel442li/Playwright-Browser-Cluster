import subprocess
import threading
import queue
import time

def read_output(out, queue, output_done):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()
    output_done.set()

# Path to your Python interpreter
python_path = "/Users/daniel-li/Code/browser-backend/venv/bin/python"
process = subprocess.Popen([python_path, '-u', '-i'],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)

output_queue = queue.Queue()
output_done = threading.Event()

output_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue, output_done))
output_thread.daemon = True
output_thread.start()

initial_commands = [
    "from playwright.sync_api import sync_playwright",
    "playwright = sync_playwright().start()",
    "browser = playwright.chromium.launch(headless=False)",
    "page = browser.new_page()",
    "page.goto('https://playwright.dev/')"
]

try:
    print("Welcome to the future")
    for command in initial_commands:
        process.stdin.write(command + "\n")
        process.stdin.flush()
        time.sleep(1)  # Give some time for command to execute

    while True:
        command = input("Enter command: ")
        if command.lower() in ["exit", "quit"]:
            break

        output_done.clear()
        process.stdin.write(command + "\n")
        process.stdin.flush()

        # Wait for output with a timeout
        timeout = 1.0  # Timeout in seconds
        start_time = time.time()
        while time.time() - start_time < timeout:
            while not output_queue.empty():
                print(output_queue.get(), end='')
            if output_done.is_set():
                break
            time.sleep(0.1)  # Sleep briefly to avoid busy waiting

except KeyboardInterrupt:
    pass
finally:
    process.stdin.close()
    process.terminate()
    process.wait()
    output_thread.join()
