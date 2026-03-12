import asyncio

from fundi import Scope, from_, ainject, scan


def require_user() -> str:
    return "user"


async def application(user: str = from_(require_user)):
    print(f"Application started with {user = }")


async def main():
    await ainject(Scope(), scan(application))


if __name__ == "__main__":
    asyncio.run(main())
