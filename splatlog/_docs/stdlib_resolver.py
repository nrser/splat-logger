from dataclasses import dataclass
from functools import cached_property
from inspect import getmembers, isclass
import sys
from importlib.machinery import ModuleSpec
from importlib.util import find_spec, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Optional, Sequence, Union


class StdlibResolver:
    """
    Resolves fully-qualified names from the standard library.

    ##### Examples #####

    Instances don't require any arguments. They also don't save any state,
    except perhaps some caching to make things quicker. The reason it's a class
    at all is that some private values are computed at initialization, and that
    could fail, so I'd rather not do it at module import.

    ```python
    >>> resolver = StdlibResolver()

    ```

    Resolves globally aviailable 'builtins'.

    This includes standard types like `str`...

    ```python
    >>> resolver.resolve_name("str")
    StdlibResolver.Resolution(name='str',
        module_spec=ModuleSpec(name='builtins', ...),
        module=<module 'builtins' (built-in)>,
        member_path=['str'],
        url='https://docs.python.org/.../library/stdtypes.html#str')

    >>> resolver.resolve_name("str").target is str
    True

    ```

    ...as well as "true" functions like `repr`...

    ```python
    >>> resolver.resolve_name("repr")
    StdlibResolver.Resolution(name='repr',
        module_spec=ModuleSpec(name='builtins', ...),
        module=<module 'builtins' (built-in)>,
        member_path=['repr'],
        url='https://docs.python.org/.../library/functions.html#repr')

    >>> resolver.resolve_name("repr").target is repr
    True

    ```

    ...exceptions such as `ValueError`...

    ```python
    >>> resolver.resolve_name("ValueError")
    StdlibResolver.Resolution(name='ValueError',
        module_spec=ModuleSpec(name='builtins', ...),
        module=<module 'builtins' (built-in)>,
        member_path=['ValueError'],
        url='https://docs.python.org/.../library/exceptions.html#ValueError')

    ```

    ...and, yes, even the lowley constants like `None`..!

    ```python
    >>> resolver.resolve_name("None")
    StdlibResolver.Resolution(name='None',
        module_spec=ModuleSpec(name='builtins', ...),
        module=<module 'builtins' (built-in)>,
        member_path=['None'],
        url='https://docs.python.org/3.10/library/constants.html#None')

    >>> resolver.resolve_name("None").target is None
    True

    ```

    Of course, we also resolve in modules you would need to import, such as
    `logging`, `typing.IO` or `inspect.Parameter.default`.

    ```python
    >>> resolver.resolve_name("logging")
    StdlibResolver.Resolution(name='logging',
        module_spec=ModuleSpec(name='logging', ...),
        module=<module 'logging' from ...>,
        member_path=[],
        url='https://docs.python.org/.../library/logging.html')

    >>> resolver.resolve_name("typing.IO")
    StdlibResolver.Resolution(name='typing.IO',
        module_spec=ModuleSpec(name='typing', ...),
        module=<module 'typing' from ...>,
        member_path=['IO'],
        url='https://docs.python.org/.../library/typing.html#typing.IO')

    >>> resolver.resolve_name("inspect.Parameter.default")
    StdlibResolver.Resolution(name='inspect.Parameter.default',
        module_spec=ModuleSpec(name='inspect', ...),
        module=<module 'inspect' from ...>,
        member_path=['Parameter', 'default'],
        url='https://docs.python.org/.../library/inspect.html#inspect.Parameter.default')

    ```
    """

    BUILTIN_CONSTANTS = (None, True, False, NotImplemented, Ellipsis, __debug__)

    @dataclass(frozen=True)
    class Resolution:
        name: str
        module_spec: ModuleSpec
        module: ModuleType
        member_path: list[str]
        url: str

        @cached_property
        def target(self) -> Any:
            return StdlibResolver.get_module_member(
                self.module, self.member_path
            )

        @cached_property
        def md_link(self) -> str:
            return "[{}]({})".format(self.name, self.url)

    @staticmethod
    def get_spec(name: str) -> Optional[ModuleSpec]:
        try:
            return find_spec(name)
        except ModuleNotFoundError:
            return None

    @staticmethod
    def module_has_member(
        module: ModuleType, member_path: Iterable[str]
    ) -> bool:
        target = module
        for name in member_path:
            if hasattr(target, name):
                target = getattr(target, name)
            else:
                return False
        return True

    @staticmethod
    def get_module_member(
        module: ModuleType, member_path: Iterable[str]
    ) -> bool:
        target = module
        for name in member_path:
            if hasattr(target, name):
                target = getattr(target, name)
            else:
                raise AttributeError(
                    "{} has no attribute '{}'".format(target, name)
                )
        return target

    @staticmethod
    def get_module(spec: ModuleSpec) -> ModuleType:
        if spec.name in sys.modules:
            return sys.modules[spec.name]

        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[spec.name] = module
        return module

    _stdlib_path: Path
    _builtin_spec: ModuleSpec
    _builtin_module: ModuleType
    _builtin_members: dict[str, Any]

    def __init__(self):
        self._stdlib_path = Path(find_spec("logging").origin).parents[1]

        self._builtin_spec = find_spec(str.__module__)
        self._builtin_module = module_from_spec(self._builtin_spec)
        self._builtin_members = dict(getmembers(self._builtin_module))

        self._url_base = "https://docs.python.org/{}.{}/library/".format(
            sys.version_info[0], sys.version_info[1]
        )

    def build_url(
        self, path: str, anchor: Union[None, str, list[str]] = None
    ) -> str:
        url = self._url_base + path

        if anchor:
            if isinstance(anchor, list):
                anchor = ".".join(anchor)
            return url + "#" + anchor

        return url

    def get_stdlib_url(
        self, module_name: str, member_path: Sequence[str] = ()
    ) -> str:
        return self.build_url(
            module_name + ".html",
            [module_name, *member_path] if member_path else None,
        )

    def is_stdlib_spec(self, spec: ModuleSpec) -> bool:
        if spec.origin == "built-in":
            return True

        try:
            Path(spec.origin).relative_to(self._stdlib_path)
        except ValueError:
            return False

        return True

    def get_stdlib_spec(self, name: str) -> Optional[ModuleSpec]:
        if spec := self.get_spec(name):
            if self.is_stdlib_spec(spec):
                return spec
        return None

    def is_builtin_name(self, name: str) -> bool:
        if "." in name:
            return False
        return name in self._builtin_members

    def is_builtin_constant(self, obj: Any) -> bool:
        for c in self.BUILTIN_CONSTANTS:
            if obj is c:
                return True
        return False

    def get_builtin_url(self, name: str) -> str:
        obj = self._builtin_members[name]

        if self.is_builtin_constant(obj):
            return self.build_url("constants.html", name)

        if isclass(obj):
            if issubclass(obj, BaseException):
                return self.build_url("exceptions.html", name)

            return self.build_url("stdtypes.html", name)

        return self.build_url("functions.html", name)

    def resolve_name(self, name: str) -> Optional[Resolution]:
        """
        This is the meat of the whole thing, and probably the only method you'll
        really need to use.

        Examples in the class doc.
        """

        if "." not in name and self.is_builtin_name(name):
            return self.Resolution(
                name=name,
                module_spec=self._builtin_spec,
                module=self._builtin_module,
                member_path=[name],
                url=self.get_builtin_url(name),
            )

        name_parts = name.split(".")
        for rindex in range(len(name_parts), 0, -1):
            module_name = ".".join(name_parts[0:rindex])
            member_path = name_parts[rindex:]

            if module_spec := self.get_stdlib_spec(module_name):
                module = self.get_module(module_spec)
                if self.module_has_member(module, member_path):
                    return self.Resolution(
                        name=name,
                        module_spec=module_spec,
                        module=module,
                        member_path=member_path,
                        url=self.get_stdlib_url(module_name, member_path),
                    )

        return None
