from collections.abc import Generator
from fundi import from_, inject, scan


class Session:
    pass


def require_session() -> Generator[Session, None, None]:
    print("Session set-up")
    yield Session()
    print("Session clean-up")


def intermediate_dependency(session: Session = from_(require_session)):
    return session


def application(
    session: Session = from_(intermediate_dependency),
    session1: Session = from_(require_session, caching=False),
):
    # session will be stored in cache and fetched on next occurrences
    # session1 will not be cached nor fetched from cache

    assert session is not session1
    print(f"Application started with {session = }")


inject({}, scan(application))
