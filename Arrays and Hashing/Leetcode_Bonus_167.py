class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        l,r = 0,len(numbers)-1
        while l<r:
            sum_res = numbers[l]+numbers[r]
            if sum_res==target:
                return [l+1,r+1]
            elif sum_res>target:
                r-=1
            else:
                l+=1
        return [-1,-1]