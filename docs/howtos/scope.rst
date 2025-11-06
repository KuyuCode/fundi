*****
Scope
*****

A scope (or context) is a dictionary that provides dynamic values that may be used by dependencies.
It should be used to provide values to dependencies through injection context. 
For example, it may be events, requests, etc.

It combines concepts from both FastAPI's and Aiogram's dependency injection systems. 
Aiogram uses parameter names to provide values to dependencies during injection,
and FastAPI uses annotations.
FunDI allows both parameter names and annotations to be used to fetch values 
from context.

  Hint: To fetch values from scope using its annotation use ``FromType[ANNOTATION]``

  Use this feature with care, as it adds additional cost in computational work.

Dependant's parameter with no :code:`from_(...)` as default value will be resolved from the **scope**

Example of dependant that use value from scope:

.. code-block:: python

    from urllib.request import Request

    from fundi import scan, inject


    def require_user(request: Request) -> str:
        user = request.get_header("User")

        if user is None:
            raise Unauthorized()

        return user


    inject({"request": Request(...)}, scan(require_user))


Dependant that use value resolved by type:

.. code-block:: python

    from urllib.request import Request

    from fundi import FromType, scan, inject


    def require_user(req: FromType[Request]) -> str:
        user = req.get_header("User")

        if user is None:
            raise Unauthorized()

        return user


    inject({"request": Request(...)}, scan(require_user))

.. warning::

    If multiple values in the scope share the same type, :code:`FromType[...]` resolution
    will prioritize the first match found. Ensure your scope is clean and well-structured.

..

  Avoid overusing scopes, as it can make debugging more difficult.
