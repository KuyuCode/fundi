from fundi import scan, from_, inject


def require_user():
    return "Alice"


def greet(user: str = from_(require_user)):
    print(f"Hello, {user}!")


inject({}, scan(greet))
