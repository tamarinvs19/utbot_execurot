from utbot_executor.deep_serialization.memory_objects import ReduceMemoryObject
from utbot_executor.deep_serialization.utils import TypeInfo


def is_numpy_ndarray(obj: object) -> bool:
    try:
        if hasattr(type(obj), '__module__') and hasattr(type(obj), '__qualname__'):
            module_check = type(obj).__module__ == 'numpy'
            name_check = type(obj).__qualname__ == 'ndarray'
            return module_check and name_check
        return False
    except Exception:
        return False
