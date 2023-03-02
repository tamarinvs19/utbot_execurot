import importlib
import json
import logging
import sys
from typing import Dict, Iterable, List, Optional, Set, Union
from utbot_executor.deep_serialization.memory_objects import (
    MemoryObject,
    ReprMemoryObject,
    ListMemoryObject,
    DictMemoryObject,
    ReduceMemoryObject,
    MemoryDump
)
from utbot_executor.deep_serialization.utils import PythonId


class MemoryObjectEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, MemoryObject):
            base_json = {
                'strategy': o.strategy,
                'id': o.id_value(),
                'kind': o.kind,
                'comparable': o.comparable,
            }
            if isinstance(o, ReprMemoryObject):
                base_json['value'] = o.value
            elif isinstance(o, (ListMemoryObject, DictMemoryObject)):
                base_json['items'] = o.items
            elif isinstance(o, ReduceMemoryObject):
                base_json['constructor'] = o.constructor
                base_json['args'] = o.args
                base_json['state'] = o.state
                base_json['listitems'] = o.listitems
                base_json['dictitems'] = o.dictitems
            return base_json
        return json.JSONEncoder.default(self, o)


class MemoryDumpEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, MemoryDump):
            return {id_: MemoryObjectEncoder().default(o) for id_, o in o.objects.items()}
        return json.JSONEncoder.default(self, o)


def as_repr_object(dct: Dict) -> Union[MemoryObject, Dict]:
    if 'strategy' in dct:
        obj: MemoryObject
        if dct['strategy'] == 'repr':
            obj = ReprMemoryObject.__new__(ReprMemoryObject)
            obj.value = dct['value']
            obj.kind = dct['kind']
            obj.comparable = dct['comparable']
            return obj
        if dct['strategy'] == 'list':
            obj = ListMemoryObject.__new__(ListMemoryObject)
            obj.items = dct['items']
            obj.kind = dct['kind']
            obj.comparable = dct['comparable']
            return obj
        if dct['strategy'] == 'dict':
            obj = DictMemoryObject.__new__(DictMemoryObject)
            obj.items = dct['items']
            obj.kind = dct['kind']
            obj.comparable = dct['comparable']
            return obj
        if dct['strategy'] == 'reduce':
            obj = ReduceMemoryObject.__new__(ReduceMemoryObject)
            obj.constructor = dct['constructor']
            obj.args = dct['args']
            obj.state = dct['state']
            obj.listitems = dct['listitems']
            obj.dictitems = dct['dictitems']
            obj.kind = dct['kind']
            obj.comparable = dct['comparable']
            return obj
    return dct


def deserialize_memory_objects(memory_dump: str) -> MemoryDump:
    parsed_data = json.loads(memory_dump, object_hook=as_repr_object)
    return MemoryDump(parsed_data['objects'])


class DumpLoader:
    def __init__(self, memory_dump: MemoryDump):
        self.memory_dump = memory_dump
        self.memory: Dict[PythonId, object] = {}  # key is new id, value is real object

    def add_syspaths(self, syspaths: Iterable[str]):
        for path in syspaths:
            if path not in sys.path:
                sys.path.append(path)

    def add_imports(self, imports: Iterable[str]):
        for module in imports:
            for i in range(1, module.count('.') + 2):
                submodule_name = '.'.join(module.split('.', maxsplit=i)[:i])
                globals()[submodule_name] = importlib.import_module(submodule_name)

    def load_object(self, python_id: PythonId) -> object:
        if python_id in self.memory:
            return self.memory[python_id]

        dump_object = self.memory_dump.objects[python_id]
        real_object: object
        if isinstance(dump_object, ReprMemoryObject):
            real_object = eval(dump_object.value)
        elif isinstance(dump_object, ListMemoryObject):
            if dump_object.kind == 'builtins.set':
                real_object = set(self.load_object(item) for item in dump_object.items)
            elif dump_object.kind == 'builtins.tuple':
                real_object = tuple(self.load_object(item) for item in dump_object.items)
            else:
                real_object = [self.load_object(item) for item in dump_object.items]
        elif isinstance(dump_object, DictMemoryObject):
            real_object = {
                    self.load_object(key): self.load_object(value)
                    for key, value in dump_object.items.items()
                    }
        elif isinstance(dump_object, ReduceMemoryObject):
            constructor = eval(dump_object.constructor)
            args = self.load_object(dump_object.args)
            real_object = constructor(*args)

            self.memory[PythonId(str(id(real_object)))] = real_object
            state = self.load_object(dump_object.state)
            for field, value in state.items():
                setattr(real_object, field, value)
            listitems = self.load_object(dump_object.listitems)
            for listitem in listitems:
                real_object.append(listitem)
            dictitems = self.load_object(dump_object.dictitems)
            for key, dictitem in dictitems.items():
                real_object[key] = dictitem
        else:
            raise TypeError(f'Invalid type {dump_object}')

        self.memory[PythonId(str(id(real_object)))] = real_object
        return real_object


def main():
    with open('test_json.json', 'r') as fin:
        data = fin.read()
    memory_dump = deserialize_memory_objects(data)
    loader = DumpLoader(memory_dump)
    loader.add_imports(['copyreg._reconstructor', 'deep_serialization.example.B', 'datetime.datetime', 'builtins.int', 'builtins.float', 'builtins.bool', 'types.NoneType', 'builtins.list', 'builtins.dict', 'builtins.str', 'builtins.tuple', 'builtins.bytes', 'builtins.type'])
    print(loader.load_object("140239390887040"))
