import typing

from utbot_executor.deep_serialization.memory_objects import MemoryDump
from utbot_executor.deep_serialization.utils import PythonId


def compress_memory(
        ids: typing.List[PythonId],
        state_before: MemoryDump,
        state_after: MemoryDump
) -> typing.Tuple[MemoryDump, MemoryDump]:
    for id_ in ids:
        if id_ in state_before.objects and id_ in state_after.objects:
            try:
                if state_before.objects[id_].obj == state_after.objects[id_].obj:
                    del state_before.objects[id_]
                    del state_after.objects[id_]
            except Exception as _:
                pass
    return state_before, state_after
