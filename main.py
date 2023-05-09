import asyncio
import json
import importlib
import pathlib
import sys


async def main():
    coin = sys.argv[1]
    config_path = pathlib.Path('config').joinpath(f'{coin}.json')

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    try:
        module = importlib.import_module(f'coins.{coin}')
    except ModuleNotFoundError:
        print(f'{coin} not supported')
        exit(-1)

    pathlib.Path('res').mkdir(exist_ok=True)
    connect = getattr(module, 'connect')

    async with asyncio.TaskGroup() as tg:
        for pool in config['pools']:
            tg.create_task(connect(pool))


if __name__ == '__main__':
    asyncio.run(main())
