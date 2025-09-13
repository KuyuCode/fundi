from contextlib import ExitStack
from typing import Annotated

from fundi import from_, inject, scan


def require_int() -> int:
    return 255


def application(value: Annotated[int, from_(require_int)], scope_value: str):
    print(f"Application started with {value = } and {scope_value = !r}")


with ExitStack() as stack:
    inject({"scope_value": "17/03/2026"}, scan(application), stack)
