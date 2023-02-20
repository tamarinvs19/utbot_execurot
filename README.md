# UtBot Executor

Util for python code execution and state serialization.

## Installation

You can install module from [https://pypi.org/project/utbot-executor/](PyPI):

```bash
python -m pip install utbot-executor
```

## Usage

### From console with socket listener

Run with your `<hostname>` and `<port>` for socket connection
```bash
$ python -m utbot_executor <hostname> <port>
```

### From code

Main method is `executor.run_calculate_function_value`.

Result format:

```json
{
        'status': 'success',
        'isException': bool,
        'statements': list[int],
        'missedStatements': list[int],
        'stateBefore': memory json dump,
        'stateAfter': memory json dump,
        'argsIds': list[str],
        'kwargs': list[str],
        'resultId': str,
}
```

States format: see [deep_serialization]()
