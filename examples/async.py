import asyncio

from fundi import from_, ainject, scan


async def require_user() -> str:
    return "user"


async def application(user: str = from_(require_user)):
    print(f"Application started with {user = }")


async def main():
    await ainject({}, scan(application))


if __name__ == "__main__":
    asyncio.run(main())
