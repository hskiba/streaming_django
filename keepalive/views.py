import asyncio

from django.http import StreamingHttpResponse


# keepalive is used to keep the connection alive
async def keepalive(q: asyncio.Queue):
    while True:
        await asyncio.sleep(1)
        await q.put("keepalive")


# primary is the main, long-running task that produces the data
async def primary(q: asyncio.Queue):
    await asyncio.sleep(5)
    await q.put('{"some": "json"}')


# long_running_task_with_keepalive is a generator that yields data
# from the primary task, and yields a space every second while the
# primary task is running to keep the connection alive.
async def long_running_task_with_keepalive():
    # create a queue to receive output from the tasks
    q = asyncio.Queue()
    # create an event loop as add the tasks to it
    loop = asyncio.get_event_loop()
    keepalive_task = loop.create_task(keepalive(q))
    loop.create_task(primary(q))

    # yield data from the queue until the primary task is done
    while True:
        item = await q.get()
        # if the item is a keepalive, send whitespace
        if item == "keepalive":
            yield " "
        # If the item is not keepalive, the primary task is done.
        # Cancel the keepalive task and return the item.
        else:
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
            yield item
            break


# Since Django's StreamingHttpResponse expects a synchronous
# iterator, we need to wrap the async generator in a synchronous generator.
# This manually creates an event loop and runs the async generator,
# yielding the results synchronously.
def sync_long_running_task_with_keepalive():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async_gen = long_running_task_with_keepalive()
    try:
        while True:
            yield loop.run_until_complete(async_gen.__anext__())
    except StopAsyncIteration:
        loop.close()


def index(request):
    response = StreamingHttpResponse(
        streaming_content=sync_long_running_task_with_keepalive(),
        content_type="text/event-stream",
    )
    return response
