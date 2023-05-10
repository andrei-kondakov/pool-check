import asyncio
import time

from coins import encode, decode, save_work


async def connect(pool):
    host, port = pool.split(':')
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except Exception as ex:
        print(f'{pool}\t{ex}')
        await connect(pool)
        return
    writer.write(encode({"id": 1, "method": "mining.subscribe", "params": ["NBMiner/39.7"]}))
    writer.write(encode({
        'id': 2,
        'method': 'mining.authorize',
        'params': [f'RHUC17zAVjNqXDtkqwLPRvQ2XgoRZsXeeG', "x"]
    }))

    while True:
        try:
            data = await reader.readline()
        except Exception as ex:
            print(f'{pool}\t{ex}')
            break

        received_at = round(time.time() * 1000)
        msg = decode(data)
        if not msg:
            break

        method = msg.get('method')

        if method != 'mining.notify':
            continue

        height = msg['params'][5]
        asyncio.create_task(save_work('rvn', pool, height, received_at, 60))

    print(f'Reconnecting to {pool}')
    await connect(pool)
