*******************
Lifespan dependency
*******************

Lifespan dependencies are dependencies with two-phase execution — preparation and tear-down.

They are usually generator-functions that ``yield`` exactly once. 
Before yielding it's a preparation, and after — tear-down. 
The yielded result would be passed to it's dependant.

Another way to define lifespan dependencies is using 
classes that implement asynchronous(``__aenter__``, ``__aexit__``) 
or synchronous(``__enter__``, ``__exit__``) context manager protocols. 
Their own dependencies can be defined inside the constructor(``__init__``).
Preparation work is done in the enter method, 
its return value is passed to the dependant.
And tear-down happens in the exit method.

  Note: implicit context managers(those created using ``contextlib.[async]contextmanager``) 
  may not be recognized automatically. They should be explicitly marked in
  ``from_(...)`` or ``scan(...)`` functions using ``context=True`` parameter.

  FunDI provides it own implementation of implicit context managers 
  that are recognized as 
  lifespan dependencies and they behave exactly as those from ``contextlib``. 
  Only difference is that both synchronous and asynchronous context managers 
  are defined using a single decorator — ``@virtual_context``

Lifespan dependencies should be used whenever tear-down logic should take the place. 
For example, closing a file, database session or releasing a lock.

Generator-function lifespan dependency
======================================

Example of dependency that acquires lock, opens file, yields it to dependant and closes file after it was used:

.. code-block:: python

    from threading import Lock

    FILE_LOCK = Lock()
    FILE_NAME = "file.txt"

    def acquire_file():
        with FILE_LOCK:
            file = open(FILE_NAME, "w+", encoding="utf-8")
            yield file
            file.close()

..

    I explicitly call :code:`file.close()` instead of using :code:`with open(...)` to make the example:

    - More readable for Python beginners

    - Avoid nested context managers

    - Clearly show when cleanup happens

Asynchronous dependency that does the same:

.. code-block:: python

    from asyncio import Lock

    FILE_LOCK = Lock()
    FILE_NAME = "file.txt"

    async def acquire_file():
        async with FILE_LOCK:
            file = open(FILE_NAME, "w+", encoding="utf-8")
            yield file
            file.close()


Context-manager lifespan dependency
===================================

You can define lifespan dependencies using class-based 
context managers — either **synchronous** (``__enter__`` / ``__exit__``) 
or **asynchronous** (``__aenter__`` / ``__aexit__``):

.. literalinclude:: ../../examples/context_manager.py


If you want to use a function as a context manager —
instead of writing a class — you can use a "virtual" context manager:

.. literalinclude:: ../../examples/virtual_context_manager.py


Exception awareness
===================
Lifespan dependencies aware about downstream exceptions. This means you can
catch exception that happened during injection in lifespan dependency to do additional
cleanup if exception occurred.

  Note: Even that lifespan dependency can catch exception does not mean it can ignore it.
  FunDI does not allow lifespan dependencies to ignore exceptions. So, exception will be re-raised
  even if lifespan dependency ignored it.

.. literalinclude:: ../../examples/lifespan_exception_awareness.py

When to use lifespan dependencies
=================================
- Managing connections
- Working with files that need cleanup
- Acquiring and releasing locks
- Wrapping external APIs that require setup/teardown
