"""Python code executor for UnitTestBot"""
import inspect
import importlib
import json
import logging
import sys
import traceback
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple
import coverage

from deep_serialization.deep_serialization import serialize_objects
from deep_serialization.json_converter import DumpLoader, deserialize_memory_objects
from deep_serialization.utils import PythonId

from utbot_executor.parser import ExecutionRequest, ExecutionResponse, ExecutionFailResponse, ExecutionSuccessResponse
from utbot_executor.utils import suppress_stdout

logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(funcName)s - %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S',
        level=logging.INFO
        )


class PythonExecutor:
    imports: Set[str]
    syspaths: List[str]

    def __init__(self):
        self.imports = set()
        self.syspaths = []

    def add_syspaths(self, syspaths: Iterable[str]):
        for path in syspaths:
            self.syspaths.append(path)
            sys.path.append(path)

    def clear_syspaths(self):
        for path in self.syspaths:
            self.syspaths -= 1
            sys.path.remove(path)

    def add_imports(self, imports: Iterable[str]):
        for module in imports:
            # submodules = module.split('.')
            # for i, _ in enumerate(submodules):
            #     fullpath = '.'.join(submodules[:i+1])
            #     if fullpath not in self.imports:
            module_name = module.split('.')[0]
            globals()[module_name] = importlib.import_module(module)
            self.imports.add(module)

    def clear_imports(self):
        for module in self.imports:
            globals().pop(module)
        self.imports.clear()

    def run_function(self, request: ExecutionRequest) -> ExecutionResponse:
        logging.debug("Prepare to run function %s", request.function_name)
        memory_dump = deserialize_memory_objects(request.serialized_memory)
        logging.debug("MemoryDump %s", memory_dump.objects)
        loader = DumpLoader(memory_dump)
        self.add_syspaths(request.syspaths)
        logging.debug("New imports %s", ", ".join(request.imports))
        self.add_imports(request.imports)
        try:
            function = getattr(
                    importlib.import_module(request.function_module),
                    request.function_name
                    )
            logging.debug("Function OK")
            args = [loader.load_object(PythonId(arg_id)) for arg_id in request.arguments_ids]
            logging.debug("Args OK")
            kwargs: dict[str, Any] = {}
        except Exception as ex:
            logging.debug("Error \n%s", traceback.format_exc())
            return ExecutionFailResponse("fail", traceback.format_exc())
        value = run_calculate_function_value(
                request.coverage_db,
                function,
                args,
                kwargs,
                request.filepath
                )
        self.clear_imports()
        self.clear_syspaths()
        return value


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
        __out_file.write(__output_data)
