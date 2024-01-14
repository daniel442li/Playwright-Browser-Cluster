import subprocess
import threading
import queue
import time
from nlp_parser import ai_command
def read_output(out, queue, output_done):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()
    output_done.set()

# Path to your Python interpreter
python_path = "/Users/daniel-li/Code/browser-backend/venv/bin/python"
process = subprocess.Popen([python_path, '-u', '-i', '-m', 'asyncio'],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)

output_queue = queue.Queue()
output_done = threading.Event()

output_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue, output_done))
output_thread.daemon = True
output_thread.start()


cookies = [{
        'name': 'li_at',
        'value': 'AQEDAStP9dYDmAa8AAABjQQs-DsAAAGNKDl8O04AtTnN10CX0bDxvPgQPWSD2YF7CIFVBbe5VfggjPe8z6rH7xcAHpi_XPSwLFhWa4BQlMy86Hw6Rlt0Dce5mc11WWGMZJpoIj_xcwTR7kFQJYYP_yI3',
        'domain': 'www.linkedin.com',
        'path': '/',
        # You can add other properties like 'expires', 'httpOnly', etc.
    }]

# initial_commands = [
#     "from playwright.sync_api import sync_playwright",
#     "playwright = sync_playwright().start()",
#     "browser = playwright.chromium.launch(headless=False)",
#     "context = browser.new_context()",
#     "page = context.new_page()",
#     "page.goto('https://playwright.dev/')",
#     "context.add_cookies(" + str(cookies) + ")"
# ]

initial_commands = [
    "from playwright.async_api import async_playwright",
    "playwright = await async_playwright().start()",
    "browser = await playwright.chromium.launch(headless=False)",
    "context = await browser.new_context()",
    "page = await context.new_page()",
    "await page.goto('https://playwright.dev/')",
    "await context.add_cookies(" + str(cookies) + ")"
    ]


try:
    print("Welcome to the future")
    for command in initial_commands:
        process.stdin.write(command + "\n")
        process.stdin.flush()
        time.sleep(1)  # Give some time for command to execute

    while True:
        command = input("Enter command: ")
        command = ai_command(command)
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