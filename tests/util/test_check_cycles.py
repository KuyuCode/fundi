import pytest

from fundi.exceptions import CyclicDependencyError
from fundi import scan, from_, inject, ainject, FromType, Scope, Type


def test_no_cycle_simple():
    def dep_a():
        return 1

    def dep_b(a: int = from_(dep_a)):
        return a + 1

    inject({}, scan(dep_b))


def test_no_cycle_chain():
    def dep_a():
        return 1

    def dep_b(a: int = from_(dep_a)):
        return a

    def dep_c(b: int = from_(dep_b)):
        return b

    inject({}, scan(dep_c))


def test_direct_cycle():
    def dep_a(x=None):
        return x

    info = scan(dep_a)
    info.parameters[0] = info.parameters[0].copy(from_=info)

    with pytest.raises(CyclicDependencyError) as exc_info:
        inject({}, info)

    assert exc_info.value.trace[-1].call is dep_a


def test_indirect_cycle():
    def dep_a(x=None):
        return x

    def dep_b(x=None):
        return x

    info_a = scan(dep_a)
    info_b = scan(dep_b)

    info_a.parameters[0] = info_a.parameters[0].copy(from_=info_b)
    info_b.parameters[0] = info_b.parameters[0].copy(from_=info_a)

    with pytest.raises(CyclicDependencyError):
        inject({}, info_a)


def test_cycle_error_message():
    def dep_a(x=None):
        return x

    info = scan(dep_a)
    info.parameters[0] = info.parameters[0].copy(from_=info)

    with pytest.raises(CyclicDependencyError) as exc_info:
        inject({}, info)

    assert "dep_a" in str(exc_info.value)


async def test_async_direct_cycle():
    async def dep_a(x=None):
        return x

    info = scan(dep_a)
    info.parameters[0] = info.parameters[0].copy(from_=info)

    with pytest.raises(CyclicDependencyError) as exc_info:
        await ainject({}, info)

    assert exc_info.value.trace[-1].call is dep_a


async def test_async_indirect_cycle():
    async def dep_a(x=None):
        return x

    async def dep_b(x=None):
        return x

    info_a = scan(dep_a)
    info_b = scan(dep_b)

    info_a.parameters[0] = info_a.parameters[0].copy(from_=info_b)
    info_b.parameters[0] = info_b.parameters[0].copy(from_=info_a)

    with pytest.raises(CyclicDependencyError):
        await ainject({}, info_a)


def test_indirect_type_factory_cycle():
    class MyType:
        pass

    def factory(dep: FromType[MyType]) -> MyType:
        return MyType()

    def target(value: FromType[MyType]):
        return value

    scope = Scope({MyType: Type.factory(factory)})

    target_info = scan(target)

    with pytest.raises(CyclicDependencyError):
        inject(scope, target_info)


async def test_async_indirect_type_factory_cycle():
    class MyType:
        pass

    async def factory(dep: FromType[MyType]) -> MyType:
        return MyType()

    async def target(value: FromType[MyType]):
        return value

    scope = Scope({MyType: Type.factory(factory)})

    target_info = scan(target)

    with pytest.raises(CyclicDependencyError):
        await ainject(scope, target_info)
