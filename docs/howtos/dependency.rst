**********
Dependency
**********


Dependencies in FunDI are simple asynchronous/synchronous functions.
That are used to create and provide data to dependants.
They help split code into preparation and actual work.

  Note: By default, each dependency is evaluated only once
  per injection cycle — subsequent uses are cached.

  To disable this behavior use :code:`caching=False` parameter in :code:`from_(...)` and :code:`scan(...)` functions

Example of dependency that generates one random name:

.. code-block:: python

    import random

    def require_random_name() -> str:
        return random.choice(
            ("Bob", "Steve", "Petro", "Yevhen", "Stepan", "Vitaliy", "Volodymyr", "Tom", "Jack", "Jerry")
        )


..

  In real apps, you can override this dependency for testing. See `overriding <overriding.html>`_ section


Asynchronous dependency is defined in the same way:

.. code-block:: python

    import random
    import asyncio

    async def require_random_name() -> str:
        await asyncio.sleep(0.4)  # simulate web request
        return random.choice(
            ("Bob", "Steve", "Petro", "Yevhen", "Stepan", "Vitaliy", "Volodymyr", "Tom", "Jack", "Jerry")
        )


Naming convention
=================
  Because :code:`get_user_or_die_trying` is a little too honest.

I'd recommend to give to dependency the name that actually represent what they provide and do.

Prefixes are good way to tell how dependency behaves on injection. Some of the prefixes I use:

- :code:`require_` - Dependency may raise error whenever something had failed
- :code:`optional_` - Dependency may return None whenever it fails
- :code:`acquire_` - Dependency acquires some resources. Used by `lifespan-dependencies <lifespan-dependency.html>`_

Also, prefixes can help you to separate dependency name from the parameter name where it's result goes.
Simplest example is :code:`admin_user` and :code:`require_admin_user`
