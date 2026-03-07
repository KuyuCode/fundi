from fundi import inject, scan, FromType, Scope, Type


class Session:
    pass


def application(
    session: FromType[Session],
):
    print(f"Application started with {session = }")


# Scope key goes to "session" parameter of application function
inject(Scope({Session: Type.instance(Session())}), scan(application))
