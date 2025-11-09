![FunDI logo](https://raw.githubusercontent.com/kuyugama/fundi/refs/heads/main/docs/_static/FunDI_horizontal.png)

# # _FunDI_
> Solution for problem no one had before

> Fun stays for function(or for fun if you wish) and DI for Dependency Injection

This library provides fast(to write!) and convenient(to use!) Dependency Injection 
for functional programming on python.

## Why?  

This library was inspired by FastAPI's dependency injection. The reasons for its existence are simple:  

- **A standalone dependency injection library.** DI shouldn't be tied to a specific framework.  
- **It simplifies code writing.** Dependency injection reduces boilerplate and improves maintainability.  
- **Lack of DI libraries for functional programming in Python.** Or maybe I just didn't want to find one :3  


## No more words, let's try!

```python
from fundi import scan, from_, inject


def require_user():
    return "Alice"


def greet(user: str = from_(require_user)):
    print(f"Hello, {user}!")


inject({}, scan(greet))
```

See the documentation to get more examples: https://fundi.readthedocs.io/en/stable/
