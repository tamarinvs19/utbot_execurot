import dataclasses
import json
from typing import Dict, Union


@dataclasses.dataclass
class ExecutionRequest:
    function_name: str
    imports: list[str]
    syspaths: list[str]
    arguments_ids: list[str]
    serialized_memory: str
    coverage_db: str
    filepath: str


class ExecutionResponse:
    status: str


@dataclasses.dataclass
class ExecutionSuccessResponse(ExecutionResponse):
    status: str
    is_exception: bool
    statements: list[int]
    missed_statements: list[int]
    state_before: str
    state_after: str
    args_ids: list[str]
    kwargs_ids: list[str]
    result_id: str


@dataclasses.dataclass
class ExecutionFailResponse(ExecutionResponse):
    status: str
    exception: Exception


def as_execution_result(dct: Dict) -> Union[ExecutionRequest, Dict]:
    if set(dct.keys()) == {'functionName', 'imports', 'argumentsIds', 'serializedMemory', 'coverageDB', 'filepath'}:
        return ExecutionRequest(
                dct['functionName'],
                dct['imports'],
                dct['argumentsIds'],
                dct['serializedMemory'],
                dct['coverageDB'],
                dct['filepath'],
                )
    return dct


def parse_request(request: str) -> ExecutionRequest:
    return json.loads(request, object_hook=as_execution_result)


def serialize_response(response: ExecutionResponse) -> str:
    return json.dumps(response)
