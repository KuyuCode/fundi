************
Side effects
************

Side effects are functions whose results are intentionally ignored.
Side effects are dependencies themselves, so they can have their own dependencies
(and even side effects ‒ though you might create a mess if go too deep).

Side effects are useful when some function should be executed **before** the 
dependency, and its result is not needed. They share the same lifespan 
as normal dependencies: if lifespan dependency is used as a side effect, 
it will be torn down **after** its dependant.

Side effects can be assigned globally(at function definition site) or 
locally(at dependant function definition site). Globally defined 
side effects execute every time their dependant is injected. 
Global side effects are additive ‒ local ones don't override them.

Side effects are executed in a special scope that provides three values:

- "``__dependant__``": the dependant's ``CallableInfo``
- "``__values__``": a dictionary of arguments that will be passed to the dependant
- "``__sccoe__``": the injection scope itself

They cannot modify the scope or the dependant since they are called after all 
values are resolved and ready for injection. Therefore, modifying the scope wouldn't make much sense anyway.

Global side effect
==================
.. code-block:: python

    import typing

    from fundi import with_side_effects, CallableInfo, inject, scan


    def side_effect(__dependant__: CallableInfo[typing.Any], __values__: dict[str, typing.Any]):
        print(__dependant__.call, "gets called with the arguments", __values__)


    @with_side_effects(side_effect)
    def app(a: int, b: str):
        print(a, b)


    inject({"a": 1, "b": "string"}, scan(app))
 

Local side effect
==================
.. code-block:: python

    import typing

    from fundi import with_side_effects, CallableInfo, inject, scan


    def side_effect(__dependant__: CallableInfo[typing.Any], __values__: dict[str, typing.Any]):
        print(__dependant__.call, "gets called with the arguments", __values__)


    def app(a: int, b: str):
        print(a, b)


    inject({"a": 1, "b": "string"}, scan(app, side_effects=(side_effect,)))
