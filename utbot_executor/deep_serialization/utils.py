import pickle
from typing import Any, NewType

PythonId = NewType('PythonId', str)


def check_comparability(py_object: object, deserialized_py_object: object) -> bool:
    return py_object == deserialized_py_object


def get_type(py_object: object) -> str:
    if py_object is None:
        return 'types.NoneType'
    if callable(py_object):
        return 'typing.Callable'
    module = type(py_object).__module__
    return '{module}.{name}'.format(
        module=module,
        name=type(py_object).__qualname__,
    )


def get_type_name(type_: type) -> str:
    if type_ is None:
        return 'types.NoneType'
    return '{module}.{name}'.format(
        module=type_.__module__,
        name=type_.__qualname__,
    )


def has_reduce(py_object: object) -> bool:
    if getattr(py_object, '__reduce__', None) is None:
        return False
    try:
        py_object.__reduce__()
        return True
    except TypeError:
        return False
    except pickle.PicklingError:
        return False
    except Exception:
        return False


def get_repr(py_object: object) -> str:
    if isinstance(py_object, type):
        return get_type_name(py_object)
    if isinstance(py_object, float):
        if repr(py_object) == 'nan':
            return "float('nan')"
        if repr(py_object) == 'inf':
            return "float('inf')"
        if repr(py_object) == '-inf':
            return "float('-inf')"
        return repr(py_object)
    if isinstance(py_object, complex):
        return f"complex(real={get_repr(py_object.real)}, imag={get_repr(py_object.imag)})"
    return repr(py_object)


def has_repr(py_object: object) -> bool:
    if isinstance(py_object, type):
        return True
    try:
        pickle.dumps(py_object)
    except pickle.PicklingError:
        return False

    try:
        r = repr(py_object)
        if not isinstance(py_object, str) and r.startswith('<') and r.endswith('>'):
            return False
    except Exception:
        return False

    return True


def getattr_by_path(py_object: object, path: str) -> object:
    current_object = py_object
    for layer in path.split("."):
        current_object = getattr(current_object, layer)
    return current_object
        
