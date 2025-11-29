from fundi import scan, from_, InjectionContext, AsyncInjectionContext


def test_sync_scope_sharing():
    with InjectionContext({"scope_value": 1}) as ctx:
        injections = 0

        def dep(scope_value: int):
            nonlocal injections
            injections += 1

            assert scope_value == 1

        ctx.inject(scan(dep))
        ctx.inject(scan(dep))

        assert injections == 2


def test_sync_cache_sharing():
    with InjectionContext() as ctx:
        injections = 0
        dep_calls = 0

        def dep():
            nonlocal dep_calls
            dep_calls += 1

        def dependant(value: None = from_(dep)):
            nonlocal injections
            injections += 1

        ctx.inject(scan(dependant))
        ctx.inject(scan(dependant))

        assert dep_calls == 1
        assert injections == 2


def test_sync_override_sharing():
    dep_calls = 0

    def dep():
        nonlocal dep_calls
        dep_calls += 1

    with InjectionContext(override={dep: 0}) as ctx:
        injections = 0

        def dependant(value: None = from_(dep)):
            nonlocal injections
            injections += 1

        ctx.inject(scan(dependant))
        ctx.inject(scan(dependant))

        assert dep_calls == 0
        assert injections == 2


def test_sync_lifecycle_sharing():
    with InjectionContext({"scope_value": 1}) as ctx:
        enters = 0
        exits = 0

        def dep(scope_value: int):
            nonlocal enters, exits
            enters += 1
            yield
            exits += 1

        ctx.inject(scan(dep))
        assert enters == 1
        assert exits == 0

        ctx.inject(scan(dep))
        assert enters == 2
        assert exits == 0

    assert exits == 2


async def test_async_scope_sharing():
    async with AsyncInjectionContext({"scope_value": 1}) as ctx:
        injections = 0

        async def dep(scope_value: int):
            nonlocal injections
            injections += 1

            assert scope_value == 1

        await ctx.inject(scan(dep))
        await ctx.inject(scan(dep))

        assert injections == 2


async def test_async_cache_sharing():
    async with AsyncInjectionContext() as ctx:
        injections = 0
        dep_calls = 0

        async def dep():
            nonlocal dep_calls
            dep_calls += 1

        async def dependant(value: None = from_(dep)):
            nonlocal injections
            injections += 1

        await ctx.inject(scan(dependant))
        await ctx.inject(scan(dependant))

        assert dep_calls == 1
        assert injections == 2


async def test_async_override_sharing():
    dep_calls = 0

    async def dep():
        nonlocal dep_calls
        dep_calls += 1

    async with AsyncInjectionContext(override={dep: 0}) as ctx:
        injections = 0

        async def dependant(value: None = from_(dep)):
            nonlocal injections
            injections += 1

        await ctx.inject(scan(dependant))
        await ctx.inject(scan(dependant))

        assert dep_calls == 0
        assert injections == 2


async def test_async_lifecycle_sharing():
    async with AsyncInjectionContext({"scope_value": 1}) as ctx:
        enters = 0
        exits = 0

        async def dep(scope_value: int):
            nonlocal enters, exits
            enters += 1
            yield
            exits += 1

        await ctx.inject(scan(dep))
        assert enters == 1
        assert exits == 0

        await ctx.inject(scan(dep))
        assert enters == 2
        assert exits == 0

    assert exits == 2
