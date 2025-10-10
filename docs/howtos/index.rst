***************
FunDI mastering
***************

Learn how to use FunDI like a pro (or at least fake it convincingly).

FunDI is a lightweight library with a focused codebase — smaller than big
frameworks like aiogram or FastAPI, but carefully crafted to solve dependency
injection in a clean, composable way.

So, let's begin our tour with basic definitions:

- Dependency - function that is used to create and/or provide data.
- Lifespan-dependency - function that creates data, provides it
  and cleans up resources. This is a simple Python generator function
  with exactly one :code:`yield`, used to manage setup and teardown.

- Dependant - function that uses other functions as dependencies.
  Can also be used as dependency.
- Scope - injection start-up environment.

Deep dive to each component

.. toctree::
    :maxdepth: 2

    dependency
    lifespan-dependency
    configurable-dependency
    dependant
    scope
    injection
    hooks
    overriding
    debugging
