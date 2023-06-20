import collections
import dataclasses
import datetime
import typing

import pytest

from utbot_executor.deep_serialization.deep_serialization import serialize_objects_dump, deserialize_objects


def template_test_assert(obj: typing.Any, imports: typing.List[str]):
    serialized_obj_ids, _, serialized_memory_dump = serialize_objects_dump([obj], True)
    deserialized_objs = deserialize_objects(serialized_obj_ids, serialized_memory_dump, imports)
    deserialized_obj = deserialized_objs[serialized_obj_ids[0]]
    assert obj == deserialized_obj


@pytest.mark.parametrize(
    'obj',
    [
        (1,),
        ('abc',),
        (1.23,),
        (False,),
        (True,),
        (b'123',),
        (r'1\n23',),
        ([1, 2, 3],),
        (['a', 2, 3],),
        ([],),
        ({1, 2},),
        (set(),),
        ({1: 2, '3': '4'},),
        ({},),
        ((1, 2, 3),),
        (tuple(),),
    ],
)
def test_primitives(obj: typing.Any):
    template_test_assert(obj, [])


@pytest.mark.parametrize(
    'obj,imports',
    [
        (datetime.datetime(2023, 6, 23), ['datetime']),
        (collections.deque([1, 2, 3]), ['collections']),
        (collections.Counter('jflaskdfjslkdruovnerjf:a'), ['collections']),
        (collections.defaultdict(int, [(1, 2)]), ['collections']),
    ],
)
def test_with_imports(obj: typing.Any, imports: typing.List[str]):
    template_test_assert(obj, imports)


@dataclasses.dataclass
class MyDataClass:
    a: int
    b: str
    c: typing.List[int]
    d: typing.Dict[str, bytes]


@pytest.mark.parametrize(
    'obj,imports',
    [
        (MyDataClass(1, 'a', [1, 2], {'a': b'c'}), ['utbot_executor.deep_serialization.tests']),
        (MyDataClass(1, 'a--------------\n\t', [], {}), ['utbot_executor.deep_serialization.tests']),
    ],
)
def test_dataclasses(obj: typing.Any, imports: typing.List[str]):
    template_test_assert(obj, imports)


class MyClass:
    def __init__(self, a: int, b: str, c: typing.List[int], d: typing.Dict[str, bytes]):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def __eq__(self, other):
        if not isinstance(other, MyClass):
            return False
        return self.a == other.a and self.b == other.b and self.c == other.c and self.d == other.d


@pytest.mark.parametrize(
    'obj,imports',
    [
        (MyClass(1, 'a', [1, 2], {'a': b'c'}), ['utbot_executor.deep_serialization.tests']),
        (MyClass(1, 'a--------------\n\t', [], {}), ['utbot_executor.deep_serialization.tests']),
    ],
)
def test_classes(obj: typing.Any, imports: typing.List[str]):
    template_test_assert(obj, imports)


class MyClassWithSlots:
    __slots__ = ['a', 'b', 'c', 'd']

    def __init__(self, a: int, b: str, c: typing.List[int], d: typing.Dict[str, bytes]):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def __eq__(self, other):
        if not isinstance(other, MyClassWithSlots):
            return False
        return self.a == other.a and self.b == other.b and self.c == other.c and self.d == other.d

    def __str__(self):
        return f'<MyClassWithSlots: a={self.a}, b={self.b}, c={self.c}, d={self.d}>'

    def __setstate__(self, state):
        for key, value in state[1].items():
            self.__setattr__(key, value)


@pytest.mark.parametrize(
    'obj,imports',
    [
        (MyClassWithSlots(1, 'a', [1, 2], {'a': b'c'}), ['utbot_executor.deep_serialization.tests', 'copyreg']),
        (MyClassWithSlots(1, 'a--------------\n\t', [], {}), ['utbot_executor.deep_serialization.tests', 'copyreg']),
    ],
)
def test_classes_with_slots(obj: typing.Any, imports: typing.List[str]):
    template_test_assert(obj, imports)
