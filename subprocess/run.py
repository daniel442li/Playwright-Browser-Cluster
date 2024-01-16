import queue
import threading
from sub import BrowserAutomation
import asyncio
# Your BrowserAutomation class definition remains the same

# Function to run BrowserAutomation in a separate thread
def start_automation(command_queue, session_id):
    async def run_automation():
        automation = BrowserAutomation(session_id, command_queue)
        await automation.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_automation())

def main():
    command_queue = queue.Queue()
    session_id = "test"  # Replace with the actual session ID

    # Start BrowserAutomation in a separate thread
    automation_thread = threading.Thread(target=start_automation, args=(command_queue, session_id))
    automation_thread.start()

    # CLI loop in the main thread
    while True:
        command = input("Enter command (type 'exit' to stop): ")
        command_queue.put(command)
        if command.lower() == 'exit':
            break

    automation_thread.join()

if __name__ == "__main__":
    main()