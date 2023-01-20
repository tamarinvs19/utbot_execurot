"""Python code executor for UnitTestBot"""
from typing import Any, Callable, Dict, List, Optional, Tuple
import json
import inspect
import coverage

from deep_serialization.deep_serialization import serialize_objects


from utbot_executor.serializer import PythonTreeSerializer
from utbot_executor.utils import suppress_stdout


def __get_lines(start, end, lines):
    return [x for x in lines if start < x < end]


def serialize_state(
        args: List[Any],
        kwargs: Dict[str, Any],
        result: Optional[Any] = None,
        ) -> Tuple[List[str], Dict[str, str], Optional[str], str]:
    all_arguments = args + list(kwargs.values()) + ([result] if result is not None else [])
    ids, serialized_memory = serialize_objects(all_arguments)
    return (
            ids[:len(args)],
            ids[len(args):len(args)+len(kwargs)],
            ids[-1] if result is not None else None,
            serialized_memory,
            )


def run_calculate_function_value(
        database_name: str,
        function: Callable,
        args: List[Any],
        kwargs: Dict[str, Any],
        fullpath: str,
        output: str
    ):
    _, _, _, state_before = serialize_state(args, kwargs)

    __cov = coverage.Coverage(
        data_file=database_name,
        data_suffix=".coverage",
    )
    __cov.start()
    try:
        with suppress_stdout():
            __result = function(*args, **kwargs)
            __status = "success"

    except Exception as __exception:
        __result = __exception
        __status = "fail"
    __cov.stop()

    (__sources, __start, ) = inspect.getsourcelines(function)
    __end = __start + len(__sources)
    (_, __stmts, _, __missed, _, ) = __cov.analysis2(fullpath)
    __cov.erase()
    __stmts_filtered = __get_lines(__start, __end, __stmts)
    __stmts_filtered_with_def = [__start] + __stmts_filtered
    __missed_filtered = __get_lines(__start, __end, __missed)

    args_ids, kwargs_ids, result_id, state_after = serialize_state(args, kwargs, __result)

    with open(output, "w", encoding="utf-8") as __out_file:
        __output_data = "\n".join([
            str(__status),
            str(__stmts_filtered_with_def),
            str(__missed_filtered),
            state_before,
            state_after,
            json.dumps(args_ids),
            json.dumps(kwargs_ids),
            str(result_id),
        ])
        __out_file.write(__output_data)


def fail_argument_initialization(output: str, exception: Exception):
    with open(output, "w", encoding="utf-8") as __out_file:
        __status = "arguments_fail"
        __output_data = "\n".join([
            str(__status),
            str(exception),
            "",
            "",
            "",
            "",
            "",
            "",
        ])
        __out_file.write(exception)
