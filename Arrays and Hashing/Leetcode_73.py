
class Solution:
    def setZeroes(self, matrix: List[List[int]]) -> None:
        length,breadth = len(matrix), len(matrix[0])

        set_y = set()
        set_x = set()

        for i in range(length):
            for j in range(breadth):
                if matrix[i][j]==0:
                    set_y.add(i)
                    set_x.add(j)
        
        for i in range(length):
            for j in range(breadth):
                if i in set_y or j in set_x:
                    matrix[i][j] = 0
                 
            
        