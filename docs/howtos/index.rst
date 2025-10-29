***************
FunDI mastering
***************

Learn how to use FunDI like a pro (or at least fake it convincingly).

FunDI is a lightweight library with a focused codebase — smaller than big
frameworks like aiogram or FastAPI, but carefully crafted to solve dependency
injection in a clean, composable way.

So, let's begin our tour with basic definitions:

- Dependency — function that is used to create and/or provide data.
- Configurable dependency — function that when called creates dependency that will be injected.
  These should be used for more complex scenarios, or generic dependencies that work based
  on context.

- Lifespan-dependency — function that creates data, provides it
  and cleans up resources. This is a simple Python generator function
  with exactly one :code:`yield`, used to manage setup and teardown.

- Dependant — function that uses other functions as dependencies.
  Can also be used as dependency.

- Scope — injection start-up environment.
- Injection — process of resolving function arguments from **scope** and its dependencies.

- Side effect — a function that is injected before a **dependant**. Unlike normal **dependencies**,
  its result is not passed to the **dependant**.

- Hook — a function that is called on certain events with a predefined set 
  of positional parameters. Hooks can affect injection behavior.

Deep dive to each component

.. toctree::
    :maxdepth: 2

    dependency
    lifespan-dependency
    configurable-dependency
    dependant
    scope
    injection
    side-effects
    hooks
    overriding
    debugging
