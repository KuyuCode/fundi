from fundi import from_, inject, scan


def require_user() -> str:
    return "user"


def application(user: str = from_(require_user)):
    print(f"Application started with {user = }")


inject({}, scan(application), override={require_user: "test_user"})
