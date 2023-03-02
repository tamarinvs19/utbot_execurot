from __future__ import annotations
from itertools import zip_longest
import pickle
from typing import Any, Dict, List, Optional, Type

from utbot_executor.deep_serialization.utils import PythonId, get_type_name, get_type, has_reduce, check_comparability, get_repr


class MemoryObject:
    strategy: str
    kind: str
    comparable: bool
    is_draft: bool
    deserialized_obj: object
    obj: object

    def __init__(self, obj: object) -> None:
        self.is_draft = True
        self.kind = get_type_name(obj) if isinstance(obj, type) else get_type(obj)
        self.obj = obj

    def _initialize(self, deserialized_obj: object = None, comparable: bool = True) -> None:
        self.deserialized_obj = deserialized_obj
        self.comparable = comparable
        self.is_draft = False

    def initialize(self) -> None:
        self._initialize()

    def id_value(self) -> str:
        return str(id(self.obj))

    def __repr__(self) -> str:
        if hasattr(self, 'obj'):
            return str(self.obj)
        return self.kind

    def __str__(self) -> str:
        return str(self.obj)



class ReprMemoryObject(MemoryObject):
    strategy: str = 'repr'
    value: str

    def __init__(self, repr_object: object) -> None:
        super().__init__(repr_object)
        self.value = get_repr(repr_object)

    def initialize(self) -> None:
        try:
            deserialized_obj = pickle.loads(pickle.dumps(self.obj))
            comparable = check_comparability(self.obj, deserialized_obj)
        except Exception:
            deserialized_obj = self.obj
            comparable = False

        super()._initialize(deserialized_obj, comparable)


class ListMemoryObject(MemoryObject):
    strategy: str = 'list'
    items: List[PythonId] = []

    def __init__(self, list_object: object) -> None:
        self.items: List[PythonId] = []
        super().__init__(list_object)

    def initialize(self) -> None:
        serializer = PythonSerializer()

        for elem in self.obj:
            elem_id = serializer.write_object_to_memory(elem)
            self.items.append(elem_id)

        deserialized_obj = [serializer[elem] for elem in self.items]
        comparable = all(serializer.get_by_id(elem).comparable for elem in self.items)

        super()._initialize(deserialized_obj, comparable)

    def __repr__(self) -> str:
        if hasattr(self, 'obj'):
            return str(self.obj)
        return f'{self.kind}{self.items}'


class DictMemoryObject(MemoryObject):
    strategy: str = 'dict'
    items: Dict[PythonId, PythonId] = {}

    def __init__(self, dict_object: object) -> None:
        self.items: Dict[PythonId, PythonId] = {}
        super().__init__(dict_object)

    def initialize(self) -> None:
        self.obj: Dict
        serializer = PythonSerializer()

        for key, value in self.obj.items():
            key_id = serializer.write_object_to_memory(key)
            value_id = serializer.write_object_to_memory(value)
            self.items[key_id] = value_id

        deserialized_obj = {
            serializer[key_id]: serializer[value_id]
            for key_id, value_id in self.items.items()
        }
        equals_len = len(self.obj) == len(deserialized_obj)
        comparable = equals_len and\
                all(serializer.get_by_id(value_id).comparable for elem in self.items)

        super()._initialize(deserialized_obj, comparable)

    def __repr__(self) -> str:
        if hasattr(self, 'obj'):
            return str(self.obj)
        return f'{self.kind}{self.items}'


class ReduceMemoryObject(MemoryObject):
    strategy: str = 'reduce'
    constructor: str
    args: PythonId
    state: PythonId
    listitems: PythonId
    dictitems: PythonId

    reduce_value: List[Any] = []

    def __init__(self, reduce_object: object) -> None:
        super().__init__(reduce_object)
        serializer = PythonSerializer()

        py_object_reduce = reduce_object.__reduce__()
        self.reduce_value = [
            default if obj is None else obj
            for obj, default in zip_longest(
                py_object_reduce,
                [None, [], {}, [], {}],
                fillvalue=None
                )
        ]

        self.constructor = get_type_name(self.reduce_value[0])
        self.args = serializer.write_object_to_memory(self.reduce_value[1])

        self.deserialized_obj = self.reduce_value[0](*serializer[self.args])

    def initialize(self) -> None:
        serializer = PythonSerializer()

        self.state = serializer.write_object_to_memory(self.reduce_value[2])
        self.listitems = serializer.write_object_to_memory(list(self.reduce_value[3]))
        self.dictitems = serializer.write_object_to_memory(dict(self.reduce_value[4]))

        deserialized_obj = self.deserialized_obj
        for key, value in serializer[self.state].items():
            object.__setattr__(deserialized_obj, key, value)
        for item in serializer[self.listitems]:
            deserialized_obj.append(item)
        for key, value in serializer[self.dictitems].items():
            deserialized_obj[key] = value

        comparable = self.obj == deserialized_obj

        super()._initialize(deserialized_obj, comparable)


class MemoryObjectProvider(object):
    @staticmethod
    def get_serializer(obj: object) -> Optional[Type[MemoryObject]]:
        pass


class ListMemoryObjectProvider(MemoryObjectProvider):
    @staticmethod
    def get_serializer(obj: object) -> Optional[Type[MemoryObject]]:
        if isinstance(obj, (list, set, tuple)):  # any(type(obj) == t for t in (list, set, tuple)):
            return ListMemoryObject
        return None


class DictMemoryObjectProvider(MemoryObjectProvider):
    @staticmethod
    def get_serializer(obj: object) -> Optional[Type[MemoryObject]]:
        if isinstance(obj, dict):  # type(obj) == dict:
            return DictMemoryObject
        return None


class ReduceMemoryObjectProvider(MemoryObjectProvider):
    @staticmethod
    def get_serializer(obj: object) -> Optional[Type[MemoryObject]]:
        if has_reduce(obj):
            return ReduceMemoryObject
        return None


class ReprMemoryObjectProvider(MemoryObjectProvider):
    @staticmethod
    def get_serializer(obj: object) -> Optional[Type[MemoryObject]]:
        return ReprMemoryObject


class MemoryDump:
    objects: Dict[PythonId, MemoryObject]

    def __init__(self, objects: Optional[Dict[PythonId, MemoryObject]] = None):
        if objects is None:
            objects = {}
        self.objects = objects


class PythonSerializer:
    memory: MemoryDump
    created: bool = False

    providers: List[MemoryObjectProvider] = [
            ListMemoryObjectProvider,
            DictMemoryObjectProvider,
            ReduceMemoryObjectProvider,
            ReprMemoryObjectProvider,
            ]

    def __new__(cls):
        if not cls.created:
            cls.instance = super(PythonSerializer, cls).__new__(cls)
            cls.memory = MemoryDump()
            cls.created = True
        return cls.instance

    def clear(self):
        self.memory = MemoryDump()

    def get_by_id(self, id_: PythonId) -> MemoryObject:
        return self.memory.objects[id_]

    def __getitem__(self, id_: PythonId) -> object:
        return self.get_by_id(id_).deserialized_obj

    def write_object_to_memory(self, py_object: object) -> PythonId:
        """Save serialized py_object to memory and return id."""

        id_ = PythonId(str(id(py_object)))
        for provider in self.providers:
            serializer = provider.get_serializer(py_object)
            if serializer is not None:
                mem_obj = serializer(py_object)
                self.memory.objects[id_] = mem_obj
                mem_obj.initialize()
                return id_

        raise ValueError(f'Can not find provider for object {py_object}.')
