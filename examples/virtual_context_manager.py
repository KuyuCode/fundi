from fundi import from_, inject, scan, virtual_context


@virtual_context
def virtual_ctx():
    print("Virtual context manager set-up")
    yield "Virtual context manager value"
    print("Virtual context manager tear-down")


def application(virtual_ctx_value: str = from_(virtual_ctx)):
    print(f"Application started with {virtual_ctx_value = }")


inject({}, scan(application))
