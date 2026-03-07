from fundi import from_, inject, scan, Scope


def require_user() -> str:
    return "user"


def test_require_user() -> str:
    return "custom_user_from_dependency"


def application(user: str = from_(require_user)):
    print(f"Application started with {user = }")


inject(Scope(), scan(application), override={require_user: scan(test_require_user)})
