from typing import Callable
from fundi import scan
from fundi.types import CallableInfo
from fundi.util import mutation


def test_default():
    mutator: Callable[[CallableInfo], CallableInfo] = mutation(lambda x: x.key.add("Kuyugama"))

    call = lambda: None
    info = scan(call)

    mutator(info)

    assert info.key._items == [call, "Kuyugama"]
