import re
from enum import Enum
from typing import Collection


class ApiSortType(Enum):
    """
    Allowed sort types on the API.
    """

    ASC = 'asc'
    DESC = 'desc'

    @classmethod
    def parse(cls, value: str) -> tuple[str, "ApiSortType"]:
        """
        Split and parse a sort string into a key and ApiSortType.

        :param value: The string to parse.
        :return: The corresponding ApiSortType.
        :raises ValueError: If the value is not a valid sort type.
        """
        tokens = value.split(":")
        key, sort_type_str = (
            (tokens[0], tokens[1].lower())
            if len(tokens) > 1
            else (tokens[0], "asc")
        )

        try:
            return key, ApiSortType(sort_type_str)
        except ValueError:
            raise ValueError(f"Invalid sort type: {sort_type_str}")


def api_split_args(value: str | Collection[str]) -> list[str]:
    """
    Split a comma-separated string or return a list as is.

    :param value: The string or collection to split.
    :return: A list of strings.
    """
    if isinstance(value, str):
        return re.split(r"\s*,\s*", value.strip())
    return list(value)