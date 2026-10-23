import pytest
from leetcode_259_3sum_smaller import threeSumSmaller


def threeSumSmaller(nums, target):
    if not nums or len(nums) < 3:
        return 0
    nums.sort()
    count = 0
    n = len(nums)
    for i in range(n - 2):
        left, right = i + 1, n - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s < target:
                count += right - left
                left += 1
            else:
                right -= 1
    return count


class TestThreeSumSmaller:
    def test_empty_list(self):
        assert threeSumSmaller([], 0) == 0

    def test_single_element(self):
        assert threeSumSmaller([1], 0) == 0
        assert threeSumSmaller([-5], 0) == 0

    def test_two_elements(self):
        assert threeSumSmaller([1, 2], 0) == 0
        assert threeSumSmaller([-1, 1], 0) == 0

    def test_basic_cases(self):
        assert threeSumSmaller([-2, 0, 1, 3], 2) == 2
        assert threeSumSmaller([1, 2, 3], 7) == 1
        assert threeSumSmaller([1, 2, 3], 6) == 1
        assert threeSumSmaller([1, 2, 3], 5) == 0

    def test_all_same(self):
        assert threeSumSmaller([1, 1, 1, 1], 4) == 4
        assert threeSumSmaller([2, 2, 2, 2], 7) == 4
        assert threeSumSmaller([0, 0, 0, 0], 1) == 4
        assert threeSumSmaller([1, 1, 1, 1, 1], 4) == 10

    def test_negative_numbers(self):
        assert threeSumSmaller([-2, -1, -3, 0], -4) == 1
        assert threeSumSmaller([-3, -2, -1, 0, 1], -3) == 3
        assert threeSumSmaller([-5, -4, -3, -2, -1], -8) == 10
        assert threeSumSmaller([-10, -5, 0, 5, 10], 0) == 8

    def test_mixed_positive_negative(self):
        assert threeSumSmaller([-3, -2, 0, 1, 2, 3], 1) == 4
        assert threeSumSmaller([-1, 0, 1, 2, 3], 3) == 3

    def test_all_negative(self):
        assert threeSumSmaller([-5, -4, -3, -2, -1], -9) == 3
        assert threeSumSmaller([-5, -4, -3, -2, -1], -11) == 10

    def test_all_positive(self):
        assert threeSumSmaller([1, 2, 3, 4, 5], 10) == 4
        assert threeSumSmaller([1, 2, 3, 4, 5], 7) == 3

    def test_duplicates(self):
        assert threeSumSmaller([1, 1, 1, 2, 2, 2], 4) == 18
        assert threeSumSmaller([0, 0, 0, 0, 0], 1) == 10
        assert threeSumSmaller([1, 1, 2, 2, 3, 3], 5) == 12

    def test_large_numbers(self):
        assert threeSumSmaller([1000000, 2000000, 3000000], 6000001) == 1
        assert threeSumSmaller([1000000, 2000000, 3000000], 6000000) == 0

    def test_target_very_negative(self):
        assert threeSumSmaller([1, 2, 3, 4], -100) == 0

    def test_target_very_positive(self):
        assert threeSumSmaller([1, 2, 3, 4], 100) == 4
        assert threeSumSmaller([-1, -2, -3, -4], 100) == 4

    def test_unsorted_input(self):
        assert threeSumSmaller([3, 1, 2, 4], 6) == 2
        assert threeSumSmaller([4, 2, 1, 3], 6) == 2

    def test_minimum_size(self):
        assert threeSumSmaller([1, 2, 3], 6) == 1
        assert threeSumSmaller([1, 2, 3], 7) == 1
        assert threeSumSmaller([1, 2, 3], 5) == 0

    def test_zero_handling(self):
        assert threeSumSmaller([0, 0, 0], 1) == 1
        assert threeSumSmaller([0, 0, 0], 0) == 0
        assert threeSumSmaller([-1, 0, 1], 1) == 1