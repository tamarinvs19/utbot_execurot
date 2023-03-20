"""Python code executor for UnitTestBot"""
import inspect
import importlib
import logging
import pathlib
import sys
import trace
import traceback
from typing import Any, Callable, Dict, Iterable, List, Tuple

from utbot_executor.deep_serialization.deep_serialization import serialize_objects
from utbot_executor.deep_serialization.json_converter import DumpLoader, deserialize_memory_objects
from utbot_executor.deep_serialization.utils import PythonId, getattr_by_path
from utbot_executor.parser import ExecutionRequest, ExecutionResponse, ExecutionFailResponse, ExecutionSuccessResponse
from utbot_executor.utils import suppress_stdout as __suppress_stdout

__all__ = ['PythonExecutor']


class PythonExecutor:
    def add_syspaths(self, syspaths: Iterable[str]):
        for path in syspaths:
            if path not in sys.path:
                sys.path.insert(0, path)

    def add_imports(self, imports: Iterable[str]):
        for module in imports:
            for i in range(1, module.count('.') + 2):
                submodule_name = '.'.join(module.split('.', maxsplit=i)[:i])
                logging.debug("Submodule #%d: %s", i, submodule_name)
                if submodule_name not in globals():
                    try:
                        globals()[submodule_name] = importlib.import_module(submodule_name)
                    except ModuleNotFoundError:
                        logging.warning("Import submodule %s failed", submodule_name)
                logging.debug("Submodule #%d: OK", i)

    def run_function(self, request: ExecutionRequest) -> ExecutionResponse:
        logging.debug("Prepare to run function `%s`", request.function_name)
        try:
            memory_dump = deserialize_memory_objects(request.serialized_memory)
            loader = DumpLoader(memory_dump)
        except Exception as ex:
            logging.debug("Error \n%s", traceback.format_exc())
            return ExecutionFailResponse("fail", traceback.format_exc())
        logging.debug("Dump loader have been created")

        try:
            logging.debug("Imports: %s", request.imports)
            logging.debug("Syspaths: %s", request.syspaths)
            self.add_syspaths(request.syspaths)
            self.add_imports(request.imports)
            loader.add_syspaths(request.syspaths)
            loader.add_imports(request.imports)
        except Exception as ex:
            logging.debug("Error \n%s", traceback.format_exc())
            return ExecutionFailResponse("fail", traceback.format_exc())
        logging.debug("Imports have been added")

        try:
            function = getattr_by_path(
                    importlib.import_module(request.function_module),
                    request.function_name
                    )
            if not callable(function):
                return ExecutionFailResponse(
                        "fail",
                        f"Invalid function path {request.function_module}.{request.function_name}"
                        )
            logging.debug("Function initialized")
            args = [loader.load_object(PythonId(arg_id)) for arg_id in request.arguments_ids]
            logging.debug("Arguments: %s", args)
            kwargs: dict[str, Any] = {}
        except Exception as ex:
            logging.debug("Error \n%s", traceback.format_exc())
            return ExecutionFailResponse("fail", traceback.format_exc())
        logging.debug("Arguments have been created")

        try:
            value = _run_calculate_function_value(
                    function,
                    args,
                    kwargs,
                    request.filepath
                    )
        except Exception as ex:
            logging.debug("Error \n%s", traceback.format_exc())
            return ExecutionFailResponse("fail", traceback.format_exc())
        logging.debug("Value have been calculated: %s", value)
        return value


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


def _run_calculate_function_value(
        function: Callable,
        args: List[Any],
        kwargs: Dict[str, Any],
        fullpath: str,
    ) -> ExecutionResponse:
    """ Calculate function evaluation result.

    Return serialized data: status, coverage info, object ids and memory."""

    _, _, _, state_before = _serialize_state(args, kwargs)

    __is_exception = False

    (__sources, __start, ) = inspect.getsourcelines(function)
    __end = __start + len(__sources)

    __tracer = trace.Trace(
        count=1,
        trace=0,
    )

    try:
        with __suppress_stdout():
            __result = __tracer.runfunc(function, *args, **kwargs)
    except Exception as __exception:
        __result = __exception
        __is_exception = True
    logging.debug("Function call finished: %s", __result)

    logging.debug("Coverage: %s", __tracer.counts)
    logging.debug("Fullpath: %s", fullpath)
    module_path = pathlib.PurePath(fullpath)
    __stmts = [x[1] for x in __tracer.counts if pathlib.PurePath(x[0]) == module_path]
    __stmts_filtered = [x for x in range(__start, __end) if x in __stmts]
    __stmts_filtered_with_def = [__start] + __stmts_filtered
    __missed_filtered = [x for x in range(__start, __end) if x not in __stmts_filtered_with_def]
    logging.debug("Covered lines: %s", __stmts_filtered_with_def)
    logging.debug("Missed lines: %s", __missed_filtered)

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
