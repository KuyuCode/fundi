from fundi import scan, inject


def application(*, app_name: str, token: str) -> int:
    if app_name == "Kat":
        return 1

    if token == "KatToken":
        return 1

    print(f'[{app_name}] user "{token}" logged in')
    return 0


exit_code = inject(
    {"app_name": "Application name", "token": "f5a7f859-8d0c-42b8-bc72-b7ea9ade0519"},
    scan(application),
)

assert exit_code == 0, "Exit code != 0"
