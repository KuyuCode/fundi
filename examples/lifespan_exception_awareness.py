from fundi import from_, scan, inject, injection_trace


def lifespan():
    try:
        yield
        print("Injection happened successfully")
    except ConnectionRefusedError as e:  # <== Lifespan dependency caught exception
        print("exception happened on teardown:", e)
        print("injection trace:")
        trace = injection_trace(e)
        while trace:
            print(" ", trace.info.call, "with", trace.values)
            trace = trace.origin

        print()


def require_random_animal(b=from_(lifespan)) -> str:
    raise ConnectionRefusedError(
        "Cannot connect to random.animal.com"
    )  # <== Exception happened here


def application(
    animal: str = from_(require_random_animal),
):
    print("Animal:", animal)


try:
    inject({}, scan(application))
except (
    ConnectionRefusedError
):  # <== Lifespan dependency does not reraise exception, but it still goes downstream
    print("ConnectionRefusedError happened on injection")
