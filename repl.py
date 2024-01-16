import subprocess
import threading
import queue
import time
import json
from nlp_parser import ai_command
def read_output(out, error, queue, output_done):
    for line in iter(out.readline, ''):
        queue.put(line)
    for line in iter(error.readline, ''):
        queue.put("ERROR: " + line)  # Prefixing errors for easier identification
    out.close()
    error.close()
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

output_thread = threading.Thread(target=read_output, args=(process.stdout, process.stderr, output_queue, output_done))
output_thread.daemon = True
output_thread.start()


cookies = [{
        'name': 'li_at',
        'value': 'AQEDAStP9dYDmAa8AAABjQQs-DsAAAGNKDl8O04AtTnN10CX0bDxvPgQPWSD2YF7CIFVBbe5VfggjPe8z6rH7xcAHpi_XPSwLFhWa4BQlMy86Hw6Rlt0Dce5mc11WWGMZJpoIj_xcwTR7kFQJYYP_yI3',
        'domain': 'www.linkedin.com',
        'path': '/',
        # You can add other properties like 'expires', 'httpOnly', etc.
    }]


#await context.add_cookies({cookies})

# async def take_screenshots(page, done, interval=0.2):
#     while not done[0]:  # Check the done flag
#         if page.is_closed():
#             break
#         if not page.is_closed():
#             screenshot_bytes = await page.screenshot(full_page=True)
#             screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
#             print(screenshot_base64)
#         await asyncio.sleep(interval)

# done = [False]
# screenshot_task = asyncio.create_task(take_screenshots(page, done))

initial_commands = '''
import base64
from playwright.async_api import async_playwright
playwright = await async_playwright().start()
browser = await playwright.chromium.launch(headless=False)
context = await browser.new_context()
page = await context.new_page()
await page.goto('https://playwright.dev/')

async def take_screenshots(page, done, interval=0.2):
    print('take_screenshots started')
    print('peepe2e')
    print('peepe2asdasdase')

done = [False]
await test_output(page, done)

'''.format(cookies=json.dumps(cookies))

# screenshot_command = [
#     "import base64",
#     "async def take_screenshots(page, done, interval=0.2):",
#     "    print('peepee')",
#     "    while not done[0]:",  # Check the done flag
#     "        if page.is_closed():",
#     "            break",
#     "        if not page.is_closed():",
#     "            screenshot_bytes = await page.screenshot(full_page=True)",
#     "            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')",
#     "            print(screenshot_base64)",  # Print the base64 string to stdout
#     "        await asyncio.sleep(interval)"
# ]

screenshot_command = [
    "async def test_output(done):",
    "    print('Test output started')",
    ""
]



try:
    print("Welcome to the future")
    process.stdin.write(initial_commands + "\n")
    process.stdin.flush()
    
    for command in screenshot_command:
        process.stdin.write(command + "\n")
        process.stdin.flush()

    while True:
        command = input("Enter command: ")
        
        if command.lower() in ["exit", "quit"]:
            break

        
        received_command = ai_command(command)

        commands = [
            "done = [False]",
            "await test_output(done)",
          #  "screenshot_task = asyncio.create_task(take_screenshots(page, done))",
            received_command,
            "done[0] = True",
            "print('peepe2e')",
            "await screenshot_task"
        ]
        
        output_done.clear()

        for command in commands:
            process.stdin.write(command + "\n")
            process.stdin.flush()

        # Wait for output with a timeout
        timeout = 10  # Timeout in seconds
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