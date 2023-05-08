import asyncio
import json
from datetime import datetime
from collections import defaultdict

import aiofiles

history = defaultdict(dict)  # height -> pool -> dt
best = {} # height -> dt


def encode(data):
    return (json.dumps(data) + '\n').encode('utf-8')


def decode(data):
    try:
        return json.loads(data.decode('utf-8').replace('\n', ''))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


async def save_work(pool, height):
    now = datetime.utcnow().timestamp()
    if height not in history:
        best[height] = now
    if pool in history[height]:
        return
    history[height][pool] = now
    diff = now - best[height]
    block_time_pct = 100 * diff / 60
    async with aiofiles.open('res.txt', mode='a') as f:
        await f.write(f'{height},{pool},{now},{diff:.2f},{block_time_pct:.2f}%\n')


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

        msg = decode(data)
        if not msg:
            break

        method = msg.get('method')

        if method != 'mining.notify':
            continue

        height = int.from_bytes(bytes.fromhex(msg['body']['header'][16:24]), 'little')
        asyncio.create_task(save_work(pool, height))

    print(f'Reconnecting to {pool}')
    await connect(pool)


async def main():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    async with asyncio.TaskGroup() as tg:
        for pool in config['pools']:
            tg.create_task(connect(pool))


if __name__ == '__main__':
    asyncio.run(main())
