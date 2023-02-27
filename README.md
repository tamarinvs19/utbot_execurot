# UtBot Executor

Util for python code execution and state serialization.

## Installation

You can install module from [PyPI](https://pypi.org/project/utbot-executor/):

```bash
python -m pip install utbot-executor
```

## Usage

### From console with socket listener

Run with your `<hostname>` and `<port>` for socket connection
```bash
$ python -m utbot_executor <hostname> <port> <logfile> [<loglevel DEBUG | INFO | ERROR>]
```

### Result format:

```json
{
        "status": "success",
        "isException": bool,
        "statements": list[int],
        "missedStatements": list[int],
        "stateBefore": memory json dump,
        "stateAfter": memory json dump,
        "argsIds": list[str],
        "kwargs": list[str],
        "resultId": str,
}
```

or error format:

```json
{
        "status": "fail",
        "exception": str (traceback),
}
```

#### States format

TODO

### Submodule `deep_serialization`

JSON serializer and deserializer for python objects

## Source

GitHub [repository](https://github.com/tamarinvs19/utbot_executor)
