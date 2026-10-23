import traceback
import ast
import sys
import io


def run_solution(code: str, s: str, numRows: int) -> str:
    """Execute the submitted Python code to solve the zigzag conversion problem."""
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        
        solution_func = local_vars.get('Solution')
        if solution_func is None:
            raise Exception("No 'Solution' class found in the code.")
        
        instance = solution_func()
        if not hasattr(instance, 'convert'):
            raise Exception("Solution class must have a 'convert' method.")
        
        result = instance.convert(s, numRows)
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def compare_outputs(expected: str, actual: str) -> bool:
    """Compare expected and actual outputs for correctness."""
    return expected == actual