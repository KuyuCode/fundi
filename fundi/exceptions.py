import typing
from types import FunctionType
from collections.abc import AsyncGenerator, Generator

from fundi.util import callable_str
from fundi.types import CallableInfo


class ScopeValueNotFoundError(ValueError):
    def __init__(self, parameter: str, info: CallableInfo[typing.Any]):
        super().__init__(
            f'Cannot resolve "{parameter}" for {callable_str(info.call)} - Scope does not contain required value'
        )
        self.parameter: str = parameter
        self.info: CallableInfo[typing.Any] = info


class GeneratorExitedTooEarly(Exception):
    def __init__(
        self,
        function: FunctionType,
        generator: AsyncGenerator[typing.Any] | Generator[typing.Any, None, None],
    ):
        super().__init__(f"Generator exited too early")
        self.function: FunctionType = function
        self.generator: AsyncGenerator[typing.Any] | Generator[typing.Any, None, None] = generator


class InvalidInitialValue(ValueError):
    """
    Initial value passed to the ``Scope`` constructor is invalid
    """

    def __init__(self, value: typing.Any):
        super().__init__(
            f"Initial value is invalid: got {value!r}, but ``TypeFactory`` or ``TypeInstance`` expected"
        )
