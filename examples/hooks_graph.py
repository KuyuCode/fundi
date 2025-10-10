from fundi import with_hooks, from_
from fundi import FromType, Parameter, scan


# Graph hook will be called only at the addition of the dependency to the dependant's parameters
@with_hooks(graph=lambda info, parameter: info.key.add(parameter.name, parameter.annotation))
def dependency(param: FromType[Parameter]):
    print(param.name)  # name of the parameter being injected to
    print(param.annotation)  # expected type of the parameter


def dependant(_: None = from_(dependency)): ...


ci_dependant = scan(dependant)
dependant_dependency = ci_dependant.named_parameters["_"].from_
assert dependant_dependency is not None
assert dependant_dependency.key._items == [  # pyright: ignore[reportPrivateUsage]
    dependency,
    "_",
    None,
]

ci_dependency = scan(dependency)
assert ci_dependency.key._items == [dependency]  # pyright: ignore[reportPrivateUsage]
