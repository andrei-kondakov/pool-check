import asyncio
from coins import encode, decode, save_work
import time


async def connect(pool):
    host, port = pool.split(':')
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except Exception as ex:
        print(f'{pool}\t{ex}')
        await connect(pool)
        return
    writer.write(encode(
        {"id": 0, "method": "mining.subscribe",
         "body": {"version": 2, "agent": "Rigel/1.4.1", "name": "wrk",
                  "publicAddress": "719e1a617a96353049f82c953938d3ca6d9e89f7ea8e88308b7ec5a3aea8cee8"}}))
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

        height = int.from_bytes(bytes.fromhex(msg['body']['header'][16:24]), 'little')
        asyncio.create_task(save_work('iron', pool, height, received_at, 60))

    print(f'Reconnecting to {pool}')
    await connect(pool)
