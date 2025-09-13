***********
Basic usage
***********

Sync
====
To use FunDI in synchronous mode you need to use :code:`inject` function and :code:`ExitStack` class

.. literalinclude:: ../examples/sync.py

Async
=====
To use FunDI with asynchronous code - you need to use :code:`ainject` function and :code:`AsyncExitStack` class

.. literalinclude:: ../examples/async.py

Mixed
=====
You can mix async and sync dependencies using :code:`ainject` function

.. literalinclude:: ../examples/mixed.py


Positional dependencies
=======================
You may want to define dependencies inside a positional parameter. To do so, you need to use ``typing.Annotated`` in pair of ``from_()``

.. literalinclude:: ../examples/positional_dependency.py
