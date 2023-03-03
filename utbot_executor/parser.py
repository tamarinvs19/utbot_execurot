import dataclasses
import json
from typing import Dict, List, Union


@dataclasses.dataclass
class ExecutionRequest:
    function_name: str
    function_module: str
    imports: List[str]
    syspaths: List[str]
    arguments_ids: List[str]
    serialized_memory: str
    filepath: str


class ExecutionResponse:
    status: str


@dataclasses.dataclass
class ExecutionSuccessResponse(ExecutionResponse):
    status: str
    is_exception: bool
    statements: List[int]
    missed_statements: List[int]
    state_before: str
    state_after: str
    args_ids: List[str]
    kwargs_ids: List[str]
    result_id: str


@dataclasses.dataclass
class ExecutionFailResponse(ExecutionResponse):
    status: str
    exception: str


def as_execution_result(dct: Dict) -> Union[ExecutionRequest, Dict]:
    if set(dct.keys()) == {
            'functionName',
            'functionModule',
            'imports',
            'syspaths',
            'argumentsIds',
            'serializedMemory',
            'filepath'
            }:
        return ExecutionRequest(
                dct['functionName'],
                dct['functionModule'],
                dct['imports'],
                dct['syspaths'],
                dct['argumentsIds'],
                dct['serializedMemory'],
                dct['filepath'],
                )
    return dct


def parse_request(request: str) -> ExecutionRequest:
    return json.loads(request, object_hook=as_execution_result)


class ResponseEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ExecutionSuccessResponse):
            return {
                "status": o.status,
                "isException": o.is_exception,
                "statements": o.statements,
                "missedStatements": o.missed_statements,
                "stateBefore": o.state_before,
                "stateAfter": o.state_after,
                "argsIds": o.args_ids,
                "kwargsIds": o.kwargs_ids,
                "resultId": o.result_id,
            }
        if isinstance(o, ExecutionFailResponse):
            return {
                "status": o.status,
                "exception": o.exception
            }
        return json.JSONEncoder.default(self, o)

def serialize_response(response: ExecutionResponse) -> str:
    return json.dumps(response, cls=ResponseEncoder)
