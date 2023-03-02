"""Python code executor for UnitTestBot"""
import inspect
import importlib
import logging
import sys
import traceback
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple
import coverage

from utbot_executor.deep_serialization.deep_serialization import serialize_objects
from utbot_executor.deep_serialization.json_converter import DumpLoader, deserialize_memory_objects
from utbot_executor.deep_serialization.utils import PythonId, getattr_by_path

from utbot_executor.parser import ExecutionRequest, ExecutionResponse, ExecutionFailResponse, ExecutionSuccessResponse
from utbot_executor.utils import suppress_stdout


class PythonExecutor:
    def add_syspaths(self, syspaths: Iterable[str]):
        for path in syspaths:
            if path not in sys.path:
                sys.path.append(path)

    def add_imports(self, imports: Iterable[str]):
        for module in imports:
            for i in range(1, module.count('.') + 2):
                submodule_name = '.'.join(module.split('.', maxsplit=i)[:i])
                globals()[submodule_name] = importlib.import_module(submodule_name)

    def run_function(self, request: ExecutionRequest) -> ExecutionResponse:
        logging.debug("Prepare to run function `%s`", request.function_name)
        memory_dump = deserialize_memory_objects(request.serialized_memory)
        loader = DumpLoader(memory_dump)
        self.add_syspaths(request.syspaths)
        self.add_imports(request.imports)
        loader.add_syspaths(request.syspaths)
        loader.add_imports(request.imports)
        try:
            function: Callable = getattr_by_path(
                    importlib.import_module(request.function_module),
                    request.function_name
                    )
            args = [loader.load_object(PythonId(arg_id)) for arg_id in request.arguments_ids]
            kwargs: dict[str, Any] = {}
        except Exception as ex:
            logging.debug("Error \n%s", traceback.format_exc())
            return ExecutionFailResponse("fail", traceback.format_exc())
        value = run_calculate_function_value(
                function,
                args,
                kwargs,
                request.filepath
                )
        logging.debug("Function execution: done")
        return value


def __get_lines(start, end, lines):
    return [x for x in lines if start < x < end]


def _serialize_state(
        args: List[Any],
        kwargs: Dict[str, Any],
        result: Any = None,
        ) -> Tuple[List[PythonId], List[PythonId], PythonId, str]:
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
        function: Callable,
        args: List[Any],
        kwargs: Dict[str, Any],
        fullpath: str,
    ) -> ExecutionResponse:
    """ Calculate function evaluation result.

    Return serialized data: status, coverage info, object ids and memory."""

    _, _, _, state_before = _serialize_state(args, kwargs)

    __is_exception = False
    __cov = coverage.Coverage(
        data_file=None,
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
