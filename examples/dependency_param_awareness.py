from fundi import scan, FromType, from_, inject, Parameter


def header(param: FromType[Parameter]) -> str:
    print("Parameter name:", param.name)
    print("Parameter annotation:", param.annotation)

    assert param.name == "token"
    assert param.annotation is str

    return f"{param.name}-{param.annotation!r}"


def application(token: str = from_(header)):
    print("Token:", token)

    assert token == f"token-{str!r}"


inject({}, scan(application))
