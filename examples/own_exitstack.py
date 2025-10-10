import time
from contextlib import ExitStack

from fundi import inject, scan, from_


def dependency(value: str = "default"):
    print("set-up")
    yield value
    print("tear-down")


def dependant(value: str = from_(dependency)):
    yield "Dependant got " + value


with ExitStack() as stack:
    value = inject({"value": "value"}, scan(dependant), stack)
    print(value)
    print("Doing some computations before dependencies would tear-down")
    time.sleep(0.8)  # simulate computations
