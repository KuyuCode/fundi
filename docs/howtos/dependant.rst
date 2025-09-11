*********
Dependant
*********

A dependant is any Python function that declares its dependencies by
setting parameter defaults to :code:`from_(...)`. They also can be used as dependencies.

  Note: By default, each dependency is evaluated only once
  per injection cycle — subsequent uses are cached.

  To disable this behavior use :code:`caching=False` parameter in :code:`from_(...)` function


Example of dependant that use dependency to get current user:

.. code-block:: python

    from fundi import from_

    from src.models import User
    from src.dependencies import require_user


    def application(user: User = from_(require_user)):
        print(f"Current user is {user}")
..

  In some cases, you may need to manually specify whether dependency is asynchronous,
  generator or context manager.
  To do so - ``from_()`` provides parameters to override default scanning 
  behavior ``from_(call, *, async_: bool, generator: bool, context: bool)``
  
  **Note** that ``async_`` may be used in combination with generator or context
  
  **Also**, FunDI will try to define this properties using function 
  return type-hint if defined. To disable this behavior use
  ``use_return_annotation=False`` parameter

You may want to wrap several dependencies together
(e.g., name + ID = username) to pass them as a single unit:

.. code-block:: python

    import random
    import secrets

    from fundi import from_

    def require_random_name() -> str:
        return random.choice(("Andriy", "Vladyslav", "Yaroslav", "Anatoliy", "Alina"))


    def require_unique_id() -> str:
        return secrets.token_hex(12)


    def require_username(
        name: str = from_(require_random_name),
        id_: str = from_(require_unique_id)
    ) -> str:
        return f"{name} - {id_}"


    def application(username: str = from_(require_username)):
        print(f"Using username {username} to hack into your wife's Instagram")


Asynchronous dependant:

.. code-block:: python

    from fundi import from_

    from src.models import User
    from src.dependencies import require_user


    async def application(user: User = from_(require_user)):
        print(f"Current user is {user}")

..

  Async dependants works exactly the same - FunDI will :code:`await` them when needed.
