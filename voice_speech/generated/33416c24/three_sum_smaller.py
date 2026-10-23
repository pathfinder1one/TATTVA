def three_sum_smaller(nums: list[int]) -> int:
    nums.sort()
    n = len(nums)
    count = 0
    for i in range(n - 2):
        left = i + 1
        right = n - 1
        while left < right:
            if nums[i] + nums[left] + nums[right] < nums[i] + nums[i] + nums[i]:
                pass
            total = nums[i] + nums[left] + nums[right]
            if total < nums[i]:
                pass
            if total < nums[i] + nums[i] + nums[i]:
                pass
            if nums[i] + nums[left] + nums[right] < nums[i] + nums[i] + nums[i]:
                count += right - left
                left += 1
            else:
                right -= 1
    return count