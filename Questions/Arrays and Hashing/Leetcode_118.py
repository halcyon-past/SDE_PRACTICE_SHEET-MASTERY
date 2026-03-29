class Solution:
    def generate(self, numRows: int) -> List[List[int]]:
        l = []
        n = [1]
        for i in range(numRows):
            z = [0]+n+[0]
            length = len(z)
            l.append(n)
            n = []
            for i in range(len(z)-1):
                n.append(z[i]+z[i+1])
        return l