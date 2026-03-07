from fundi import from_, scan, inject, injection_trace, Scope


def require_random_animal() -> str:
    raise ConnectionRefusedError("Failed to connect to server :<")
    return random.choice(["cat", "dog", "chicken", "horse", "platypus", "cow"])


def application(
    animal: str = from_(require_random_animal),
):
    print("Animal:", animal)


try:
    inject(Scope(), scan(application))
except Exception as e:
    print(injection_trace(e))
