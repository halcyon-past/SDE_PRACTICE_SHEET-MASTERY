class Solution:
    #notes 
    """"
    option 1: sets length mismatch
    option 2: tally every number iteratively
    option 3: sort and check the number next to it is same or not
    option 4: check count of number
    """
    def containsDuplicate(self, nums: List[int]) -> bool:
        nums.sort()
        for i in range(len(nums)-1):
            if nums[i]==nums[i+1]:
                return True
        return False

