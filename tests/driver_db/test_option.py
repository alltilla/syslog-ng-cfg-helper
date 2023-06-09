from typing import Set

import json
import pytest

from syslog_ng_cfg_helper.driver_db.exceptions import MergeException
from syslog_ng_cfg_helper.driver_db.option import Option, Params


def test_named_defaults() -> None:
    option_1 = Option()

    assert option_1.name is None
    assert option_1.params == set()

    option_2 = Option("name", {("param-1",), ("param-2",)})

    assert option_2.name == "name"
    assert option_2.params == {("param-1",), ("param-2",)}


def test_eq() -> None:
    assert Option("name-1", {("param-1",)}) == Option("name-1", {("param-1",)})
    assert Option("name-1", {("param-1",)}) != Option("name-2", {("param-1",)})
    assert Option("name-1", {("param-1",)}) != Option("name-1", {("param-1", "param-2")})
    assert Option("name-1", {("param-1",)}) != Option(params={("param-1",)})
    assert Option("name-1", {("param-1",)}) != ("name-1", {("param-1",)})


def test_merge() -> None:
    option = Option("name", {("param-1",), ("param-2",)})
    option.merge(Option("name", {("param-2",), ("param-3",)}))

    assert option.params == {
        ("param-1",),
        ("param-2",),
        ("param-3",),
    }


def test_merge_different() -> None:
    option_1 = Option("name-1", set())
    option_2 = Option("name-2", set())
    option_3 = Option(params=set())

    with pytest.raises(MergeException):
        option_1.merge(option_2)

    with pytest.raises(MergeException):
        option_1.merge(option_3)


def test_copy() -> None:
    params: Set[Params] = {("param-1",)}
    option = Option("name", params)

    params.clear()
    assert option.params == {("param-1",)}

    clone = option.copy()
    assert id(option) != id(clone)

    option.merge(Option("name", {("param-2",)}))

    assert option.params == {("param-1",), ("param-2",)}
    assert clone.params == {("param-1",)}


@pytest.mark.parametrize(
    "name, params, expected_str",
    [
        (
            "name-1",
            set(),
            "name-1()",
        ),
        (
            "name-2",
            {tuple()},
            "name-2()",
        ),
        (
            "name-3",
            {("param-1", "param-2")},
            "name-3(param-1 param-2)",
        ),
        (
            "name-4",
            {("param-1", "param-2"), ("param-3", "param-4")},
            "name-4(\n    param-1 param-2\n    param-3 param-4\n)",
        ),
        (
            None,
            {("param-1", "param-2"), ("param-3", "param-4")},
            "param-1 param-2\nparam-3 param-4",
        ),
        (
            None,
            None,
            "",
        ),
    ],
    ids=range(6),
)
def test_str(name, params, expected_str) -> None:
    option = Option(name, params)
    assert str(option) == expected_str


def test_named_repr() -> None:
    option = Option("name", {("param-1", "param-2"), ("param-3", "param-4")})
    assert (
        repr(option) == "Option('name', frozenset({('param-1', 'param-2'), ('param-3', 'param-4')}))"
        or repr(option) == "Option('name', frozenset({('param-3', 'param-4'), ('param-1', 'param-2')}))"
    )


@pytest.mark.parametrize(
    "option",
    [
        Option("name", {("param-1", "param-2"), ("param-3", "param-4")}),
        Option(None, {("param-1", "param-2"), ("param-3", "param-4")}),
        Option(None, None),
    ],
    ids=range(3),
)
def test_serialization(option: Option) -> None:
    serialized = json.dumps(option.to_dict())
    deserialized = Option.from_dict(json.loads(serialized))

    assert option == deserialized
