*********
Injection
*********


Injection is the main purpose of this library. This is the process of making it all work and sound.

Injection can be
    Synchronous — performed by :code:`inject` function.
    Supports only synchronous dependencies and dependants.
    If any dependency or dependant is asynchronous — use :code:`ainject` instead.

    Asynchronous — performed by :code:`ainject` function.
    Supports both async and sync dependencies and dependants.
    **FunDI handles both sync and async dependencies transparently, even if they’re mixed.**

      Note that synchronous dependencies would not be called in a thread. 
      So it is safe to do event-loop related stuff in synchronous dependencies.


Example of synchronous injection:

.. code-block:: python

    import secrets
    from contextlib import ExitStack

    from fundi import from_, scan, inject


    def require_unique_id() -> str:
        return secrets.token_hex(12)


    def application(username: str, user_id: str = from_(require_unique_id)) -> None:
        print(f"Application started with {user_id = } and {username = }")


    inject({"username": "Kuyugama"}, scan(application))


Example of asynchronous injection:

.. code-block:: python

    import secrets
    import asyncio
    from contextlib import AsyncExitStack

    from fundi import from_, scan, ainject


    async def require_user(username: str) -> str:
        await asyncio.sleep(0.4)  # pretend to be making web request
        return {"id": secrets.token_hex(12), "username": username}


    def application(user: dict[str, str] = from_(require_user)) -> None:
        print(f"Application started with {user['id'] = } and {user['username'] = }")


    async def main():
        ainject({"username": "Kuyugama"}, scan(application))

    if __name__ == "__main__":
        asyncio.run(main())

Example of injection that produces value:

.. code-block:: python

    import secrets
    from contextlib import ExitStack

    from fundi import scan, inject


    def require_unique_id() -> str:
        return secrets.token_hex(12)


    user_id = inject({}, scan(require_user_id))
    print("Generated user id is", user_id)

..

    The same works with asynchronous injection


Own exit stack
==============
You may want to control when dependencies are torn down. 
To do so, provide your own exit stack. When you need dependencies to be torn down, 
simply close the stack — that’s it!

Synchronous example
-------------------

.. literalinclude:: ../../examples/own_exitstack.py

Asynchronous example
--------------------

.. literalinclude:: ../../examples/own_exitstack_async.py
..


    In earlier versions, FunDI required an explicit ExitStack or AsyncExitStack to 
    be provided for every injection.

    It is now optional — if not provided, FunDI will create and manage one automatically.
    

Dependency parameter awareness
==============================
Sometimes dependencies need to know *where* they are being injected.

With **dependency parameter awareness**, FunDI makes the `fundi.Parameter`
object of the target parameter available for any dependency that declares:

.. code-block:: python

    from fundi import FromType, Parameter

    def dependency(param: FromType[Parameter]):
        print(param.name)        # name of the parameter being injected to
        print(param.annotation)  # expected type of the parameter
        ...

..

  Note:
  Parameter-aware dependencies (i.e., those that accept a :code:`FromType[Parameter]`)
  are cached just like any other dependency by default.

  This means that even if the same function is injected into multiple parameters
  (e.g., :code:`user_id`, :code:`client_id`), it will only be called once, and the cached
  result will be reused — regardless of which parameter it's injected into.

  If your function depends on the parameter name or annotation (e.g. to extract different headers),
  you must disable caching manually using :code:`from_(..., caching=False)`.

  This behavior is intentional for now and may change in future versions,
  but currently it's the developer’s responsibility to manage it.

This allows you to build smarter and more reusable dependencies, such as:

- Automatically inferring names (e.g. :code:`user_id: int = from_header()` → :code:`X-User-Id` from parameter name)
- Performing type conversion or validation based on annotation

Example
-------

 .. literalinclude:: ../../examples/dependency_param_awareness.py

Summary
=======

+--------------------------------+--------------------+------------------------+
| Feature                        | :code:`inject`     | :code:`ainject`        |
+================================+====================+========================+
| Sync dependencies only         | Yes                | Yes                    |
+--------------------------------+--------------------+------------------------+
| Async dependencies             | No                 | Yes                    |
+--------------------------------+--------------------+------------------------+
| Mixed (sync + async)           | No                 | Yes                    |
+--------------------------------+--------------------+------------------------+
| Exit stack                     | :code:`ExitStack`  | :code:`AsyncExitStack` |
+--------------------------------+--------------------+------------------------+
| Dependency parameter awareness | Yes                | Yes                    |
+--------------------------------+--------------------+------------------------+
| Returns value                  | Yes                | Yes                    |
+--------------------------------+--------------------+------------------------+
