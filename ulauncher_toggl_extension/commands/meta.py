from __future__ import annotations

import enum
import logging
import math
from abc import abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Generic,
    Optional,
    Sequence,
    TypeVar,
)

from toggl_api import JSONCache
from toggl_api.models import TogglClass

from ulauncher_toggl_extension.images import (
    APP_IMG,
    PREV_IMG,
    START_IMG,
    TIP_IMAGES,
    TipSeverity,
)
from ulauncher_toggl_extension.query import Query
from ulauncher_toggl_extension.utils import quote_member, show_notification

if TYPE_CHECKING:
    from httpx import BasicAuth

    from ulauncher_toggl_extension.extension import TogglExtension

log = logging.getLogger(__name__)


class ActionEnum(enum.Enum):
    """All possible actions in ulauncher to decouple commands from the
    Ulauncher API.
    """

    LIST = enum.auto()
    CLIPBOARD = enum.auto()
    DO_NOTHING = enum.auto()
    HIDE = enum.auto()
    OPEN = enum.auto()
    OPEN_URL = enum.auto()
    RENDER_RESULT_LIST = enum.auto()
    RUN_SCRIPT = enum.auto()
    SET_QUERY = enum.auto()


ACTION_TYPE = Optional[ActionEnum | Callable | str]


@dataclass(frozen=True)
class QueryResults:
    icon: Path = APP_IMG
    name: str | None = ""
    description: str | None = ""
    on_enter: ACTION_TYPE = ActionEnum.DO_NOTHING
    on_alt_enter: ACTION_TYPE = ActionEnum.DO_NOTHING
    small: bool = False


class Singleton(type):
    _instances: dict[type, Singleton] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


T = TypeVar("T", bound=TogglClass)


class Command(Generic[T], metaclass=Singleton):
    """General base class for all commands.

    Contains a few helper methods to build up a list of utilties to quickly
    prototype a command.

    Creates a call stack that goes as follows:
        preview() -> view() -> handle()

    Methods:
        preview: Preview method of the command to show up as the extension. Abstract.
        view: View method for providing quick options, hints and anything thats
            not the command itself. Abstract.
        handle: Executes the actual command logic.
        process_model: Generates a viewable query from a Toggl object.
        call_pickle: Calls a pickled command.
        pagination: Helper method for creating paginated results.
        handler_error: Helper method for handling and dispatching consistent errors.

    Attributes:
        OPTIONS: Special symbols that can be used to trigger auto complete and
            set various values.
        PREFIX: Prefix of the command.
        ALIASES: Alternate prefixes of the command.
        EXPIRATION: Invalidation time of the cache.
        expiration: Overrides EXPIRATION if set by user.
        cache_path: Location of the cache file.
        ICON: Base icon of the command.
        ESSENTIAL: Whether the command will be used in a submenu.
        prefix: User set application prefix. Usually defaults to "tgl".
    """

    OPTIONS: ClassVar[tuple[str, ...]]
    MIN_ARGS: ClassVar[int] = 2
    PREFIX: ClassVar[str] = ""
    ALIASES: ClassVar[tuple[str, ...]]
    EXPIRATION: ClassVar[timedelta] = timedelta(weeks=1)
    ICON: ClassVar[Path] = APP_IMG
    ESSENTIAL: ClassVar[bool] = False
    # NOTE: This could be refactored into a method as some commands are situational.

    __slots__ = (
        "auth",
        "cache_path",
        "expiration",
        "max_results",
        "prefix",
        "workspace_id",
    )

    def __init__(self, extension: TogglExtension | Command) -> None:
        self.prefix: str = extension.prefix
        self.max_results: int = extension.max_results
        self.auth: BasicAuth = extension.auth
        self.workspace_id: int = extension.workspace_id
        self.cache_path: Path = Path(extension.cache_path)
        self.expiration: timedelta = extension.expiration or self.EXPIRATION

    @abstractmethod
    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        """Preview method of the command to show up as the extension prefix is
        called by the user.
        """

    @abstractmethod
    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        """View method as the method is called by the user.

        Essentially a method for a user calling the alt modifier.

        If its a direct match the extension usually will call this instead of
        the preview method.

        Some children might not need this to be implemented.
        """

    def handle(self, query: Query, **kwargs: Any) -> bool | list[QueryResults]:
        """Executes the actual command logic.

        Some children might not need this to be implemented.

        Base implementation creates subcommands based on a selected models which
        have ESSENTIAL marked as true.

        Returns:
            bool | list: Whether the command was successful or not. Will decide
                whether ulauncher closes or resets to the default command or
                another set of commands which finalise the users journey.
        """
        model = kwargs.get("model")
        base = self.__class__.__base__
        if base is None or model is None:
            return False
        results: list[QueryResults] = self.process_model(
            model,
            partial(
                self.call_pickle,
                "handle",
                query=query,
                **kwargs,
            ),
            advanced=True,
            fmt_str="{name}",
        )

        for item in base.__subclasses__():
            if not item.ESSENTIAL:
                continue
            cmd = item(self)
            results.append(
                QueryResults(
                    cmd.ICON,
                    f"{cmd.PREFIX.title()} {model.name}",
                    "",
                    partial(
                        cmd.call_pickle,
                        "handle",
                        query=query,
                        **kwargs,
                    ),
                    small=True,
                ),
            )

        return results

    @classmethod
    def call_pickle(
        cls,
        method: str,
        extension: TogglExtension | Command,
        *args,
        **kwargs,
    ) -> Any:
        """Helper method to call a pickled command."""
        log.info(
            'Pickling method "%s" for %s!',
            method,
            cls.__name__,
            extra={"arguments": args, "kwargs": kwargs},
        )
        d = cls(extension)
        return getattr(d, method)(*args, **kwargs)

    def process_model(
        self,
        model: T,
        action: ACTION_TYPE,
        alt_action: Optional[ACTION_TYPE] = None,
        *,
        advanced: bool = False,
        fmt_str: str = "{prefix} {name}",
    ) -> list[QueryResults]:
        """Helper method to create result content."""
        del advanced
        model_name = quote_member(self.PREFIX, model.name)
        return [
            QueryResults(
                self.ICON,
                fmt_str.format(prefix=self.PREFIX.title(), name=model_name),
                "",
                action,
                alt_action,
            ),
        ]

    def _paginator(
        self,
        query: Query,
        data: list[partial] | list[QueryResults],
        static: Sequence[QueryResults] = (),
        *,
        page: int = 0,
    ) -> list[QueryResults]:
        """Helper method for creating paginated results.

        Inserts bookends with prev, next page commands and alternate commands
        going to the first and last page respectively.

        Args:
            data: List of data to paginate.
            static: Default commands that every page should have.
            page: Current page number.

        Returns:
            list: List of QueryParameters to display.
        """
        page_data: list[QueryResults] = list(static)
        extra = len(page_data) + 1

        results_per_page = self.max_results - extra
        total_pages = (math.ceil(len(data) / results_per_page)) - 1

        for t in data[results_per_page * page : results_per_page * (page + 1)]:
            if isinstance(t, QueryResults):
                page_data.append(t)
            else:
                page_data.append(t()[0])

        if len(data) > self.max_results and page < total_pages:
            page_data.append(
                QueryResults(
                    START_IMG,
                    "Next Page",
                    f"{page + 2}/{total_pages + 1}",
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        data=data,
                        page=page + 1,
                    ),
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        data=data,
                        page=total_pages,
                    ),
                    small=True,
                ),
            )
        if page > 0:
            page_data.append(
                QueryResults(
                    PREV_IMG,
                    "Previous Page",
                    f"{page}/{total_pages + 1}",
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        data=data,
                        page=page - 1,
                    ),
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        data=data,
                        page=0,
                    ),
                    small=True,
                ),
            )
        return page_data

    def amend_query(self, query: list[str]) -> None:
        if not query:
            query.append(self.PREFIX)

        elif len(query) >= 2 and query[1] != self.PREFIX:  # noqa: PLR2004
            query[1] = self.PREFIX

    def notification(
        self,
        msg: str,
        on_close: Optional[Callable] = None,
    ) -> None:
        show_notification(msg, self.ICON.absolute(), on_close=on_close)

    def handle_error(self, error: Exception) -> None:
        log.error("%s", error)
        self.notification(str(error))

    @property
    def cache(self) -> JSONCache[T]:
        return JSONCache(self.cache_path, self.EXPIRATION)

    @classmethod
    def check_autocmp(cls, query: list[str]) -> bool:
        """Simple helper for verfying if a autocomplet can be used."""
        return len(query) >= cls.MIN_ARGS and any(
            query[-1][0] == x for x in cls.OPTIONS
        )

    @classmethod
    def hint(cls) -> list[QueryResults]:
        """Returns a list of hints for the command."""
        desc = cls.__doc__.split(".")[0] + "." if cls.__doc__ else ""
        hints: list[QueryResults] = [
            QueryResults(
                cls.ICON,
                cls.PREFIX.title(),
                desc,
            ),
            QueryResults(
                TIP_IMAGES[TipSeverity.INFO],
                "Prefix",
                cls.PREFIX,
            ),
            QueryResults(
                TIP_IMAGES[TipSeverity.INFO],
                "Aliases",
                ", ".join(cls.ALIASES),
            ),
        ]
        if cls.OPTIONS:
            hints.append(
                QueryResults(
                    TIP_IMAGES[TipSeverity.INFO],
                    "Accepts Options",
                    ", ".join(cls.OPTIONS),
                    small=True,
                ),
            )
            hints += [
                QueryResults(
                    TIP_IMAGES[TipSeverity.INFO],
                    label,
                    desc,
                    small=False,
                )
                for label, desc in Query.option_descriptions(frozenset(cls.OPTIONS))
            ]

        return hints

    @abstractmethod
    def get_models(self, query: Query, **kwargs: Any) -> list[T]:
        """Method that collects a list of Toggl objects.

        Will usually apply some sort of sorting and filtering before returning.

        Returns:
            list: A selection of models that were gathered.
        """

    @abstractmethod
    def get_model(self, model: T | int | str | None) -> T | None:
        """Abstract method for querying for a single model."""


class SubCommand(Command[T]):
    """Base class for all subcommands.

    Methods:
        view: View method of the subcommand which rounds up commands associated
            with the subcommand.
        amend_query: Overriden helper method to amend the query as there are
            two different prefixes for calling a subcommand.
        get_cmd: Generate the command for the subcommand
    """

    MIN_ARGS: ClassVar[int] = 3
    OPTIONS = ()

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del query, kwargs
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        preview: list[QueryResults] = []
        for sub in self.__class__.__subclasses__():
            cmd = sub(self)
            if query.subcommand and (
                query.subcommand == cmd.PREFIX
                or any(x == query.subcommand for x in cmd.ALIASES)
            ):
                return cmd.view(query, **kwargs)
            prev = cmd.preview(query, **kwargs)
            if prev:
                preview.append(prev[0])

        return preview

    def amend_query(self, query: list[str]) -> None:
        base = self.__class__.__base__
        if base is None:
            query[0] = self.PREFIX
            if len(query) > 1:
                query[1] = base.PREFIX

    def get_cmd(self) -> str:
        cmd = f"{self.prefix}"
        base = self.__class__.__base__
        if base is not None:
            cmd += f" {base.PREFIX}"

        cmd += f" {self.PREFIX}"

        return cmd
