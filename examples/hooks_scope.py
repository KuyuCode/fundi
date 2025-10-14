from fundi import scan
from fundi import inject, with_hooks


# Graph hook will be called only at the addition of the dependency to the dependant's parameters
@with_hooks(scope=lambda scope, ci: scope.update(name="Kuyugama") if "name" not in scope else None)
def dependency(name: str):
    print(f"dependency({name=!r})")


inject({}, scan(dependency))
