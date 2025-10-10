from contextlib import ExitStack

from fundi import from_, inject, scan


class RequireSession:
    def __enter__(self):
        print("Session set-up")
        return "session"

    def __exit__(self, *_):
        print("Session tear-down")
        return False


def application(session: str = from_(RequireSession)):
    print(f"Application started with {session = }")


inject({}, scan(application))
