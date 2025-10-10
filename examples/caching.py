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
    session: Session = from_(require_session), session1: Session = from_(intermediate_dependency)
):
    assert session is session1
    print(f"Application started with {session = }")


inject({}, scan(application))
