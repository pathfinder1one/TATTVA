import sys

def three_sum_smaller(nums, target):
    nums.sort()
    count = 0
    n = len(nums)
    for i in range(n - 2):
        j = i + 1
        k = n - 1
        while j < k:
            if nums[i] + nums[j] + nums[k] < target:
                count += k - j
                j += 1
            else:
                k -= 1
    return count


def run_demo():
    print("Demo: 3Sum Smaller")
    print("-" * 30)
    
    test_cases = [
        ([-2, 0, 1, 3], 2),
        ([-2, 0, 1, 3], 0),
        ([], 0),
        ([1], 0),
        ([1, 2], 0),
        ([1, 2, 3], 1),
        ([1, 2, 3], 7),
        ([-1, 0, 1, 2, -1, -4], 2),
        ([0, 0, 0, 0], 1),
        ([-1000, -1000, -1000, 1000, 1000, 1000], 500),
    ]
    
    for nums, target in test_cases:
        result = three_sum_smaller(nums, target)
        print(f"nums={nums}, target={target} => {result}")
    
    print("-" * 30)


def run_tests():
    test_cases = [
        ([-2, 0, 1, 3], 2, 2),
        ([-2, 0, 1, 3], 0, 1),
        ([], 0, 0),
        ([1], 0, 0),
        ([1, 2], 0, 0),
        ([1, 2, 3], 1, 0),
        ([1, 2, 3], 7, 1),
        ([1, 2, 3], 6, 1),
        ([1, 2, 3], 5, 1),
        ([1, 2, 3], 4, 1),
        ([1, 2, 3], 3, 0),
        ([-1, 0, 1, 2, -1, -4], 2, 3),
        ([0, 0, 0, 0], 1, 4),
        ([0, 0, 0, 0], 0, 0),
        ([1, 1, 1, 1], 4, 1),
        ([1, 1, 1, 1], 5, 4),
        ([-1000, -1000, -1000, 1000, 1000, 1000], 500, 18),
        ([2, 2, 2, 2, 2], 7, 10),
        ([2, 2, 2, 2, 2], 6, 0),
        ([1, 2, 3, 4, 5, 6], 10, 10),
        ([-2, -1, 0, 1, 2, 3], 4, 12),
        ([10, 20, 30, 40, 50], 100, 10),
        ([10, 20, 30, 40, 50], 50, 0),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 25, 35),
    ]
    
    passed = 0
    failed = 0
    
    for nums, target, expected in test_cases:
        result = three_sum_smaller(nums, target)
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"FAILED: nums={nums}, target={target}, expected={expected}, got={result}")
    
    print(f"Tests: {passed} passed, {failed} failed out of {len(test_cases)}")
    
    if failed == 0:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    run_demo()
    run_tests()