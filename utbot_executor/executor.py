"""Python code executor for UnitTestBot"""
from typing import Any, Callable, Dict, List, Tuple
import json
import inspect
import coverage

from deep_serialization.deep_serialization import serialize_objects
from deep_serialization.json_converter import DumpLoader, deserialize_memory_objects

from utbot_executor.parser import ExecutionRequest, ExecutionResponse, ExecutionFailResponse, ExecutionSuccessResponse
from utbot_executor.utils import suppress_stdout


class PythonExecutor:
    def __init__(self):
        pass

    def run_function(self, request: ExecutionRequest) -> ExecutionResponse:
        memory_dump = deserialize_memory_objects(request.serialized_memory)
        loader = DumpLoader(memory_dump)
        loader.add_syspaths(request.syspaths)
        loader.add_imports(request.imports)
        try:
            function = globals()[request.function_name]
            args = [loader.load_objects(arg_id) for arg_id in request.arguments_ids]
            kwargs: dict[str, Any] = {}
        except Exception as ex:
            return ExecutionFailResponse("fail", ex)
        return run_calculate_function_value(
                request.coverage_db,
                function,
                args,
                kwargs,
                request.filepath
                )


def __get_lines(start, end, lines):
    return [x for x in lines if start < x < end]


def _serialize_state(
        args: List[Any],
        kwargs: Dict[str, Any],
        result: Any = None,
        ) -> Tuple[List[str], List[str], str, str]:
    """Serialize objects from args, kwargs and result.

    Returns: tuple of args ids, kwargs ids, result id and serialized memory."""

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
        # output: str
    ) -> ExecutionResponse:
    """ Calculate function evaluation result.

    Return serialized data: status, coverage info, object ids and memory."""

    _, _, _, state_before = _serialize_state(args, kwargs)

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

    args_ids, kwargs_ids, result_id, state_after = _serialize_state(args, kwargs, __result)

    return ExecutionSuccessResponse(
            status="success",
            is_exception=__is_exception,
            statements=__stmts_filtered_with_def,
            missed_statements=__missed_filtered,
            state_before=state_before,
            state_after=state_after,
            args_ids=args_ids,
            kwargs_ids=kwargs_ids,
            result_id=result_id,
            )


def fail_argument_initialization(output: str, exception: Exception):
    """Save exception to output file"""
    with open(output, "w", encoding="utf-8") as __out_file:
        __output_data = json.dumps({
            "status": "fail",
            'exception': exception,
        })
        __out_file.write(exception)
