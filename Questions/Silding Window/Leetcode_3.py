class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        d = {}
        l, r = 0, 0
        res = 0
        
        while r < len(s):
            # 1 & 2. Check if the CURRENT character (r) is a duplicate.
            # If so, move the left pointer past its last seen position.
            if s[r] in d:
                l = max(l, d[s[r]] + 1)
                
            # Update the latest index of the current character
            d[s[r]] = r
            
            # 3. Calculate max length BEFORE incrementing r
            res = max(res, r - l + 1)
            
            # Move right pointer to expand window
            r += 1
            
        return res