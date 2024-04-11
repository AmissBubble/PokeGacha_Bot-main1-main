import asyncio
import time

async def cancel_me():
    print(' before sleep')

    try:
        # Wait for 1 hour
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print(' cancel sleep')
    finally:
        print(' after sleep')

async def main():
    # Create a "cancel_me" Task
    task = asyncio.create_task(cancel_me())

    # Wait for 1 second
    print(task)
    await asyncio.sleep(5)
    print('waiting 1 second')
    task.cancel()


asyncio.run(main())