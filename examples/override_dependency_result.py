from fundi import from_, inject, scan, Scope


def require_user() -> str:
    return "user"


def application(user: str = from_(require_user)):
    print(f"Application started with {user = }")


inject(Scope(), scan(application), override={require_user: "test_user"})
