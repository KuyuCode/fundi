*****
Hooks
*****

Hooks can be used to modify FunDI's injection 
process on specific dependencies.
All hooks must be synchronous functions as they should work both in asynchronous and synchronous scopes.

Graph hook
==========
Graph hook is a hook that is called when dependency is added to dependency graph.
This may be useful to modify dependency cache key depending on the dependant's parameter info.

Graph hook function is called with two positional arguments: 

- ``CallableInfo`` - information about the dependency that is about to be added to a graph
- ``Parameter`` - information about the parameter the dependency is about to be linked to

Graph hook **should modify** the CallableInfo passed to it. 
It may return anything, but returned value would **not** be used.

Here is an example:

.. literalinclude:: ../../examples/hooks_graph.py



Scope hook
==========
Scope hook is called when dependency is about to be injected. 
This hook should be used to produce dependency specific scope values.

This hook will be added in future releases.


Combining hooks
===============
It is possible to combine multiple hooks together using the ``fundi.util.combine_hooks()``.
This function will call all hooks with the same parameters and produce nothing.
