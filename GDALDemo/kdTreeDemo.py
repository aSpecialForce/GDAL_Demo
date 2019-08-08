# _*_ coding: utf-8 _*_
from pykdtree import kdtree
import numpy as np

import matplotlib.pyplot as plt

def MyKdtreeTest():
    data_pts = np.arange(25)
    kdtree2 = kdtree.KDTree(data_pts, leafsize=15)
    query_pts2 = np.arange(28,27,-1)
    dist2, idx2 = kdtree2.query(query_pts2,2)
    #assert idx[0] == 400
    #assert dist[0] == 0
    #assert idx[1] == 390

    #num_list = np.arange(12).reshape(6,2)
    num_list=np.array([[2,13],[5,4],[14,7],[18,21],[7,2],[2,9],[12,13],[15,4],[14,27],[8,11],[7,12],[12,9],
                       [22,3],[5,24],[4,27],[8,21],[7,22],[22,9],[32,13],[35,4],[14,37],[38,11],[37,12],
                       [32,39],[22,33],[35,24],[24,27],[28,21],[27,22],[22,29],[32,13],[35,14],[14,37],[38,21],
                       [37,32],[12,39],[32,33],[5,1],[22,33],[11,12],[22,30],[12,21],[23,33],[41,24]])#定义矩阵
    mytree = kdtree.KDTree(num_list)
    
    testp=np.array([[35,28]])#定义矩阵
    find_p_num=6
    dist, idx=mytree.query(testp,find_p_num)

    plt.scatter(num_list.T[0], num_list.T[1],c='g')
    plt.scatter(testp[0][0],testp[0][1],c='r')
    for i in range(find_p_num):
        plt.scatter(num_list[idx[0][i]][0], num_list[idx[0][i]][1],marker='x',c='r')
    plt.show()

if __name__ == '__main__':
    MyKdtreeTest()

    input()
    