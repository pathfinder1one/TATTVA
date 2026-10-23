def validate_input(nums: list[int]) -> None:
    if not isinstance(nums, list):
        raise TypeError("Input must be a list")
    for i, val in enumerate(nums):
        if not isinstance(val, int):
            raise TypeError(f"Element at index {i} must be an int, got {type(val).__name__}")


def generate_test_cases() -> list[list[int]]:
    cases = [
        [2, 2, 2, 2],
        [-3, -2, -1, 0, 1, 2, 3],
        [1, 1, 1, 1, 1],
        [],
        [0],
        [0, 0, 0],
        [1, 2, 3],
        [-1, 0, 1, 2, -1, -4],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        [-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
        [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        [-100, -50, 0, 50, 100],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    return cases