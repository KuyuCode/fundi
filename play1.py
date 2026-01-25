import typing

from fundi import Parameter, CallableInfo, scan, inject


def some(a: int, b: int) -> int:
    return a + b


T = typing.TypeVar("T")
cinfo = scan(some)


class InteractiveParameters:
    def __init__(self, parameters: list[Parameter]):
        self.parameters: dict[str, Parameter] = {
            parameter.name: parameter for parameter in parameters
        }
        self.__parameters_raw: list[Parameter] = parameters

    def __trigger_update(self):
        self.__parameters_raw[::] = list(self.parameters.values())

    def __getattr__(self, name: str) -> Parameter:
        if name in self.parameters:
            parameter = self.parameters[name]

        else:
            parameter = self.parameters[name] = Parameter(name, typing.Any, None)
            self.__trigger_update()

        return parameter

    def __delattr__(self, name: str) -> None:
        if name not in self.parameters:
            return None

        del self.parameters[name]
        self.__trigger_update()


class InteractiveModifier(typing.Generic[T]):
    def __init__(self, ci: CallableInfo[T]):
        self.ci: CallableInfo[T] = ci

    def parameters(self) -> InteractiveParameters:
        return InteractiveParameters(self.ci.parameters)


mod = InteractiveModifier(cinfo)
params = mod.parameters()
params.a.name = "waffel"

print(cinfo.parameters[0])
print(inject({"waffel": 1, "b": 2}, cinfo))
