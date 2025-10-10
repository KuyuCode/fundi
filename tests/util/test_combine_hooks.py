from typing import Callable
from fundi import scan
from fundi.types import CallableInfo
from fundi.util import combine_hooks


def test_default():
    mutator: Callable[[CallableInfo], CallableInfo] = combine_hooks(
        lambda x: x.key.add("Kuyugama"), lambda x: x.key.add("Hikamiya")
    )

    call = lambda: None
    info = scan(call)

    mutator(info)

    assert info.key._items == [call, "Kuyugama", "Hikamiya"]
