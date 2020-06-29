from django.test import TestCase

# Create your tests here.
def maopao(al):
    #  循环次数
    for j in range(len(al)-1,0,-1):
        # 7 6 5 4 3 2 1
        # 6 5 4 3 2 1
        # 5 4 3 2 1
        for i in range(j):
            # 0 1 2 3 4 5 6
            # 索引取值，相邻对比，如果前面比后面大，就交换位置
                 # 0  54     # 1 22
            if al[i] > al[i+1]:   # TRUE
                al[i],al[i+1] = al[i+1],al[i]

aa =[54,22,44,33,18,8,25,16]
maopao(aa)
print(aa)