*********
Debugging
*********

You made it to the final chapter. You're no longer just a user — you're a practitioner of FunDI!

Testing is good, but debugging is what separates the script kiddie from the software monk

FunDI provides useful functions to help you debug and optimize your dependency injection:
    - :code:`tree` - Generates a tree that shows how dependencies will be resolved — including resolution order and value mapping.

      .. code-block:: python

        from fundi import tree, scan

        print(tree({"username": "user"}, scan(application)))

      Outputs::

        {'call': <function application at ...>, 'values': {'username': 'user', 'user': {'call': <function require_user at ...>, 'values': {'username': 'user'}}}}

      Each node contains the function being called (:code:`call`) and the values being injected into it (:code:`values`).

    - :code:`order` - generates list that contains order in which dependencies will be called.

        Note: Result does not include function that is being passed to :code:`order` function.

      .. code-block:: python

        from fundi import order, scan

        print(order({"username": "user"}, scan(application)))

      Outputs::

        [<function require_user at ...>]

      Want more details? Try :code:`tree()`. Want less pain? Good luck.


Exceptions
==========

During injection exception may be raised, so you need to know everything about them.

Scope value not found
---------------------

If scope hadn't request by dependency value - FunDI would raise :code:`ScopeValueNotFoundError`

Tracing
-------

FunDI helps you understand direct cause of exceptions and place where did they happen -
library adds its injection trace to exception.

.. code-block:: python

    from contextlib import ExitStack

    from fundi import from_, scan, inject, injection_trace


    def require_random_animal() -> str:
        raise ConnectionRefusedError("Failed to connect to server :<")
        return random.choice(["cat", "dog", "chicken", "horse", "platypus", "cow"])


    def application(
        animal: str = from_(require_random_animal),
    ):
        print("Animal:", animal)


    try:
        inject({}, scan(application))
    except Exception as e:
        print(injection_trace(e))

Output would be::

    InjectionTrace(info=CallableInfo(call=<function application at ...>, ...), values={}, origin=InjectionTrace(info=CallableInfo(call=<function require_random_animal at ...>, ...), values={}, origin=None))

