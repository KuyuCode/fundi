from fundi import scan
from fundi import inject, with_hooks


# Scope hook will be called before the injection
@with_hooks(scope=lambda scope, ci: scope.update(name="Kuyugama") if "name" not in scope else None)
def dependency(name: str):
    print(f"dependency({name=!r})")


inject({}, scan(dependency))
