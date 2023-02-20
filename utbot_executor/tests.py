from executor import run_calculate_function_value


def func(a, b, *, c , d):
    return a + b + c + d


class A:
    def __init__(self, x):
        self.x = x

    def func(self, a, b, *, c, d):
        return a + b + c + d + self.x


# def test_run_function():
#     run_calculate_function_value(
#         'database_func',
#         func,
#         [1, 2],
#         {'c': 3, 'd': 4},
#         'tests.py',
#         'test_output_1'
#     )
#     with open('test_output_1', 'r') as out:
#         actual = [line.strip() for line in out.readlines()]
#
#     expected = [
#         'success',
#         '{"json": {"type": "builtins.int", "value": "10", "strategy": "repr", "comparable": true}, "memory": {}}',
#         '[4, 5]',
#         '[]'
#     ]
#
#     assert actual == expected
#
#
# def test_run_method():
#     a = A(100)
#     run_calculate_function_value(
#         'database_func_A',
#         a.func,
#         [1, 2],
#         {'c': 3, 'd': 4},
#         'tests.py',
#         'test_output_2'
#     )
#     with open('test_output_2', 'r') as out:
#         actual = [line.strip() for line in out.readlines()]
#
#     expected = [
#         'success',
#         '{"json": {"type": "builtins.int", "value": "110", "strategy": "repr", "comparable": true}, "memory": {}}',
#         '[12, 13]',
#         '[]'
#     ]
#
#     assert actual == expected

def append(x): x.append(1)

def test_state():
    x = [1, 2]
    run_calculate_function_value(
        'database_func_append',
        append,
        [],
        {'x': x},
        'tests.py',
        'test_output_3',
    )

test_state()

