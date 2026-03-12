from fundi import Scope, from_, inject, scan


def require_user() -> str:
    return "user"


def application(user: str = from_(require_user)):
    print(f"Application started with {user = }")


inject(Scope(), scan(application))
