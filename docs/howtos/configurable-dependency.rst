********************************
Configurable dependency(factory)
********************************

Configurable dependencies are simple functions that produce dependencies. 
They should be used to create dependencies with different 
behavior based on the arguments passed to them.


.. literalinclude:: ../../examples/configurable_dependency.py

..

  Note: ``@configurable_dependency`` is optional, but it caches dependencies,
  so their results can be cached on injection.

  Also, ``@configurable_dependency`` does not cache dependencies configured with mutable arguments.

Composite dependencies
======================
Composite dependencies are a special kind of configurable dependency that accept other
dependencies as parameters. 

These are a kind of `higher-order functions <https://en.wikipedia.org/wiki/Higher-order_function>`_,
but with DI.

.. literalinclude:: ../../examples/composite_dependency.py


Dependency configuration
========================
When a configurable dependency is called, FunDI stores its configuration,
so third-party tools (e.g. routers, docs generators, validators) can extract the metadata.

To get configuration of already scanned(using ``fundi.scan.scan``) dependency —
you can use ``CallableInfo.configuration`` attribute

If dependency is not scanned — use ``is_configured(call)`` function to check whether dependency is configured:

.. literalinclude:: ../../examples/configurable_check.py

And to get dependency configuration use ``get_configuration(call)``  function on dependency callable:

.. literalinclude:: ../../examples/configurable_config.py
