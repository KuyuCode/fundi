import asyncio
from contextlib import AsyncExitStack

from fundi import inject, scan, from_


def dependency(value: str = "default"):
    print("set-up")
    yield value
    print("tear-down")


def dependant(value: str = from_(dependency)):
    yield "Dependant got " + value


async def main():
    async with AsyncExitStack() as stack:
        value = inject({"value": "value"}, scan(dependant), stack)
        print(value)
        print("Doing some computations before dependencies would tear-down")
        await asyncio.sleep(0.8)  # simulate computations


if __name__ == "__main__":
    asyncio.run(main())
