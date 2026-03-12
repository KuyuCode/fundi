*****
Scope
*****

A scope (or context) is an object that provides dynamic values that may be used by dependencies.
It should be used to provide values to dependencies through injection context.
For example, it may be events, requests, etc.

The central piece of FunDI's dependency injection system is the :code:`fundi.Scope` object. It has three internal stores for providing values to dependants:

* Named values: for resolving dependencies by parameter name.
* Typed instances: for resolving dependencies by type annotation.
* Type factories: for resolving dependencies by type annotation, but creating the instance on-demand.

Creating a Scope
================

You can create an empty scope or initialize it with a dictionary of named values, typed instances, or type factories.

.. code-block:: python

    from fundi import Scope, Type

    # Create an empty scope
    scope = Scope()

    # Create a scope with initial named values
    scope = Scope({"user_id": 123, "request_id": "abc"})

    # Create a scope with a typed instance
    class DBConnection:
        ...
    db_conn = DBConnection()
    scope = Scope({DBConnection: Type.instance(db_conn)})

    # Create a scope with a type factory
    def create_db_connection() -> DBConnection:
        return DBConnection()
    scope = Scope({DBConnection: Type.factory(create_db_connection)})


Adding Values
=============

You can add named values to the scope using the :code:`add_value` method or by initializing the scope with a dict.

.. code-block:: python

    scope.add_value("user_name", "Alice")

Adding Typed Instances
======================

You can add instances that will be resolved by their type.

.. code-block:: python

    class DBConnection:
        ...

    db_conn = DBConnection()
    scope.add_type(db_conn)

    # A dependant can now receive the DBConnection instance by type
    def my_dependency(db: DBConnection):
        ...

Adding Type Factories
=====================

Type factories are callables that produce an instance of a certain type when it's requested. This is useful for resources that should be created on-demand.

The ``add_factory`` method is highly flexible. You can provide the type explicitly, or ``fundi`` can infer it from the factory's return type annotation.

.. code-block:: python

    # Explicitly providing the type
    def create_db_connection() -> DBConnection:
        return DBConnection()

    scope.add_factory(create_db_connection, DBConnection)

    # Inferring the type from the return annotation
    def create_another_connection() -> AnotherConnection:
        return AnotherConnection()

    scope.add_factory(create_another_connection)


Additionally, you can pass parameters from the ``scan()`` function directly to ``add_factory`` to control caching and other behaviors.

.. code-block:: python

    # Adding a factory with caching enabled
    def create_cached_service() -> CachedService:
        print("Creating new CachedService instance")
        return CachedService()

    scope.add_factory(create_cached_service, caching=True)

    # The factory will be called only once for the first dependant that needs a CachedService.
    # Subsequent requests will receive the cached instance.
    def my_dependency(service: CachedService):
        ...

Mutual Exclusivity
------------------
A type can either have an instance or a factory, but not both. When you add a new instance or factory for a given type, any existing instance or factory for that same type will be removed to prevent conflicts.

Updating a Scope
================

You can update an existing scope with new values, instances, or factories using the :code:`update` method.

.. code-block:: python

    import logging
    from fundi import Scope, Type

    scope = Scope({"user_id": 1})

    class Request:
        ...
    request_instance = Request()

    def create_logger() -> logging.Logger:
        return logging.getLogger(__name__)

    scope.update(
        {
            Request: Type.instance(request_instance),
            logging.Logger: Type.factory(create_logger),
        },
        request_id="xyz",
    )
    # The scope now contains "user_id", "request_id", Request instance, and a factory for logging.Logger.

Resolving Dependencies
======================

FunDI resolves dependencies from the scope in the following order:

1. By parameter name (matching named values in the scope).
2. By type annotation (matching a typed instance or a type factory in the scope).

Example of a dependant that uses a value from the scope:

.. code-block:: python

    from fundi import Scope, inject, scan

    def require_user(user_name: str) -> str:
        if user_name == "Alice":
            return "Welcome, Alice!"
        raise ValueError("Unknown user")

    scope = Scope({"user_name": "Alice"})
    inject(scope, scan(require_user))


Dependant that uses a value resolved by type:

.. code-block:: python

    from fundi import Scope, inject, scan

    class Request:
        def __init__(self, user: str):
            self._user = user

        def get_header(self, name: str) -> str | None:
            if name == "User":
                return self._user
            return None

    def require_user(request: Request) -> str:
        user = request.get_header("User")
        if user is None:
            raise ValueError("Unauthorized")
        return user

    scope = Scope()
    scope.add_type(Request("bob"))
    inject(scope, scan(require_user))

.. _from-legacy-scopes:

Working with Legacy Scopes
==========================

To maintain backward compatibility, FunDI can automatically convert legacy dictionary-based scopes into :code:`Scope` objects. You can also do this manually using the :code:`from_legacy` class method.

.. code-block:: python

    from fundi import Scope

    legacy_scope = {"request": Request("charlie")}
    scope = Scope.from_legacy(legacy_scope)

Merging Scopes
==============

You can merge two scopes using the :code:`|` operator or the :code:`merge` method. If there is a conflict between a typed instance and a factory, the instance will be kept.

.. code-block:: python

    scope1 = Scope({"a": 1})
    scope2 = Scope({"b": 2})
    merged_scope = scope1 | scope2  # or scope1.merge(scope2)
    assert merged_scope["a"] == 1
    assert merged_scope["b"] == 2
