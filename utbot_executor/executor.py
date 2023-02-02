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
        result: Any = None,
        ) -> Tuple[List[str], List[str], str, str]:
    all_arguments = args + list(kwargs.values()) + [result]
    ids, serialized_memory = serialize_objects(all_arguments)
    return (
            ids[:len(args)],
            ids[len(args):len(args)+len(kwargs)],
            ids[-1],
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

    __is_exception = False
    __cov = coverage.Coverage(
        data_file=database_name,
        data_suffix=".coverage",
    )
    __cov.start()
    try:
        with suppress_stdout():
            __result = function(*args, **kwargs)
    except Exception as __exception:
        __result = __exception
        __is_exception = True
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
        __output_data = json.dumps({
            "status": "success",
            "isException": __is_exception,
            "statements": __stmts_filtered_with_def,
            "missedStatements": __missed_filtered,
            "stateBefore": state_before,
            "stateAfter": state_after,
            "argsIds": args_ids,
            "kwargsIds": kwargs_ids,
            "resultId": result_id,
        })
        __out_file.write(__output_data)


def fail_argument_initialization(output: str, exception: Exception):
    with open(output, "w", encoding="utf-8") as __out_file:
        __output_data = json.dumps({
            "status": "fail",
            'exception': exception,
        })
        __out_file.write(exception)
