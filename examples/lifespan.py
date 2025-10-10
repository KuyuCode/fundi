from collections.abc import Generator

from fundi import from_, inject, scan


def require_session() -> Generator[str, None, None]:
    print("Session set-up")
    yield "session"
    print("Session clean-up")


def application(session: str = from_(require_session)):
    print(f"Application started with {session = }")


inject({}, scan(application))
