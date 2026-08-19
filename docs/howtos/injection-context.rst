*****************
Injection Context
*****************

Injection contexts allow you to share scope, cache, overrides and lifecycle
between multiple injections.

There are two flavors of injection context:

    :code:`InjectionContext` — synchronous injection context.
    Allows only synchronous dependencies of all kinds to be injected.

    :code:`AsyncInjectionContext` — asynchronous injection context.
    Allows both synchronous and asynchronous dependencies of all kinds to be injected.

Example:

.. code-block:: python

    from fundi import InjectionContext, scan

    with InjectionContext({"global_": 10}) as ctx:
        ctx.inject(scan(lambda global_: print(global_)))  # 10
        ctx.scope["global_"] = 20  # update context scope

        # Create sub context which will be closed automatically with parent
        sub = ctx.sub()
        sub.inject(scan(lambda global_: print(global_)))  # 20

        # Injection nesting
        def dependant(sub: FromType[InjectionContext]):
            # context passed into dependencies is the sub context of the context
            # it was called with
            assert sub != ctx
            sub.inject(scan(another_dependant))

        ctx.inject(scan(dependant))

        # Create context copy, it will not be closed automatically
        with ctx.copy() as copy:
            copy.inject(scan(lambda global_: print(global_)))  # 20

..

    :code:`AsyncInjectionContext` works the same way, but every method that
    performs injection or creates a sub context is a coroutine and must be
    awaited.


Creating a context
===================

Both context types accept the same set of arguments on construction:

.. code-block:: python

    from fundi import InjectionContext, Scope

    ctx = InjectionContext(
        scope={"username": "Kuyugama"},  # or a fundi.Scope instance
        cache=None,                      # optional pre-populated cache
        override=None,                   # optional dependency overrides
    )

- :code:`scope` — initial scope of the context. Accepts a plain mapping or a
  :code:`fundi.Scope` instance. If a plain mapping is provided, it is
  converted via :code:`Scope.from_legacy`.
- :code:`cache` — initial cache used to store results of cached dependencies.
  A shallow copy is taken, so the original mapping is not mutated.
- :code:`override` — mapping of dependency callables to their overrides. A
  shallow copy is taken as well.

Injecting within a context
===========================

.. code-block:: python

    ctx.inject(info, scope=None, override=None, no_cache=False)

    # Asynchronous equivalent
    await actx.inject(info, scope=None, override=None, no_cache=False)

:code:`inject` uses the scope, cache, exit stack and overrides defined on the
context itself:

- The provided :code:`scope` argument is merged on top of the context's own
  scope.
- The merged scope automatically exposes the context itself under the
  :code:`fundi.InjectionContext` (or :code:`fundi.AsyncInjectionContext`)
  type, bound to a sub context of the context the injection was called with.
  This is what enables the *injection nesting* shown in the example above.
- The provided :code:`override` argument is merged on top of the context's
  own overrides.
- If :code:`no_cache` is :code:`True`, the context's cache is bypassed
  entirely — dependency results are neither read from nor written to it.

..

  Injected dependency can request injection context using :code:`FromType[<injection context type>]`. 
  The resulting context will inherit data from its parent context data and will be linked to its lifespan. 
  This isolates nested injections but still shares configuration.

  Be aware: injected lifespan-dependencies are closed only at injection context closure. 
  This means that you need to be very wary about injection context usage and coverage.
  For example, if your application handles incoming requests and you have global injection context 
  and want to share its data with request handlers you should copy the global injection context and 
  NOT make a subcontext. This will ensure that all request-related dependencies are closed in time.


Sub contexts
============

.. code-block:: python

    sub = ctx.sub(scope=None, override=None, no_cache=False)

    # Asynchronous equivalent
    sub = await actx.sub(scope=None, override=None, no_cache=False)

:code:`sub` creates a copy of the context (see :code:`copy` below) and
attaches it to the lifecycle of the parent context — the sub context is
closed automatically whenever the parent context is closed.

Copying a context
==================

.. code-block:: python

    copy = ctx.copy(scope=None, override=None, no_cache=False)

    # Asynchronous equivalent — copy() itself is not a coroutine,
    # it only builds a new AsyncInjectionContext instance
    copy = actx.copy(scope=None, override=None, no_cache=False)

:code:`copy` creates a new, independent context:

- :code:`scope` is merged with the context's own scope.
- :code:`override` is merged with the context's own overrides.
- Unless :code:`no_cache` is :code:`True`, the cache is copied as well
  (shallow copy).

Unlike :code:`sub`, a copy is **not** tied to the parent's lifecycle — it
must be entered and closed on its own, typically via a :code:`with`
(or :code:`async with`) statement.

Lifecycle
=========

Both context types are context managers and can be used with :code:`with`
(:code:`InjectionContext`) or :code:`async with` (:code:`AsyncInjectionContext`).

.. code-block:: python

    with InjectionContext() as ctx:
        ...
    # ctx.close() is called automatically here

    async with AsyncInjectionContext() as actx:
        ...
    # await actx.close() is called automatically here

They can also be closed manually:

.. code-block:: python

    ctx.close()

    # Asynchronous equivalent
    await actx.close()

Closing a context tears down every pending lifespan-dependency injected
through it, and through any of its sub contexts. If the context is closing
due to an exception, that exception is raised inside the pending
dependencies, just like with a regular :code:`ExitStack` /
:code:`AsyncExitStack`.

Summary
=======

+--------------------------+--------------------------+-------------------------------+
| Feature                  | :code:`InjectionContext` | :code:`AsyncInjectionContext` |
+==========================+==========================+===============================+
| Sync dependencies        | Yes                      | Yes                           |
+--------------------------+--------------------------+-------------------------------+
| Async dependencies       | No                       | Yes                           |
+--------------------------+--------------------------+-------------------------------+
| Mixed (sync + async)     | No                       | Yes                           |
+--------------------------+--------------------------+-------------------------------+
| Exit stack               | :code:`ExitStack`        | :code:`AsyncExitStack`        |
+--------------------------+--------------------------+-------------------------------+
| Nested / sub contexts    | Yes                      | Yes                           |
+--------------------------+--------------------------+-------------------------------+
| Independent copies       | Yes                      | Yes                           |
+--------------------------+--------------------------+-------------------------------+
| Cache & override sharing | Yes                      | Yes                           |
+--------------------------+--------------------------+-------------------------------+
