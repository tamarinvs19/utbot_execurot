import datetime
import json
from pprint import pprint

from utbot_executor.deep_serialization.memory_objects import PythonSerializer
from utbot_executor.deep_serialization.json_converter import MemoryDumpEncoder
from utbot_executor.deep_serialization.deep_serialization import deserialize_objects


class B:
    def __init__(self, b1, b2, b3):
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.time = datetime.datetime.now()


def run():
    from pprint import pprint

    c = ["Alex"]
    b = B(1, 2, 3)
    b.b1 = B(4, 5, b)
    a = [1, 2, float('inf'), "abc", {1: 1}, None, b, c]
    serializer_ = PythonSerializer()
    pprint(serializer_.write_object_to_memory(a))
    pprint(serializer_.memory.objects)
    with open('test_json.json', 'w') as fout:
        print(json.dumps({'objects': serializer_.memory}, cls=MemoryDumpEncoder, indent=True), file=fout)


def deserialize():
    # run()
    with open('test_json.json', 'r') as fin:
        data = fin.read()
    print(data)
    pprint(deserialize_objects(["139825536103424"], data, [
        'copyreg',
        'utbot_executor.deep_serialization.example',
        'datetime'
    ]))


if __name__ == '__main__':
    deserialize()
