class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        maxSum = -float(inf)
        curr = 0
        for num in nums:
            curr += num
            if curr>maxSum:
                maxSum=curr
            if curr<0:
                curr=0
        return maxSum