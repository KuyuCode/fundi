**********
Overriding
**********

Dependency overriding is a feature that allows you to override dependency or its result.

You can override either:
    Dependency result — the dependency callable will not be executed; 
    instead, the provided value will be used.

    Dependency callable — you can override one dependency with another

Overriding result:
    :code:`override={require_user: test_user}`
    → FunDI will skip calling :code:`require_user` and use :code:`test_user` instead.

Overriding callable:
    :code:`override={require_user: scan(mock_user_func)}`
    → FunDI will call :code:`mock_user_func` instead of :code:`require_user`.


Example of overriding dependency result:

.. code-block:: python

    from fundi import scan, inject

    from src import application
    from src.models import User
    from src.dependencies import require_user


    test_user = User(
        id="test-id",
        username="test_user",
    )

    inject({"username": test_user.username}, scan(application), override={require_user: test_user})


Example of overriding dependency callable:

.. code-block:: python

    from contextlib import ExitStack

    from fundi import scan, inject

    from src import application
    from src.models import User
    from src.dependencies import require_user


    test_user = User(
        id="test-id",
        username="test_user",
    )


    def test_require_user() -> User:
        return test_user


    inject({"username": test_user.username}, scan(application), override={require_user: scan(test_require_user)})

