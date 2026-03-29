class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        idx = 0
        num = 0
        flag = False
        for i in range(len(nums)-2,-1,-1):
            if nums[i]<nums[i+1]:
                num = nums[i]
                idx = i
                flag = True
                break
        if not flag:
            nums.reverse()
            return
        for i in range(len(nums)-1,idx,-1):
            if nums[i]>num:
                print(f"idx: {idx}, num: {num}, idx2: {i}: num2: {nums[i]}")
                nums[i],nums[idx]=nums[idx],nums[i]
                break
        nums[idx+1:] = reversed(nums[idx+1:])