
import matplotlib.pyplot as plt 
import matplotlib as mpl 
import numpy as np 
 
from sklearn import datasets 
from sklearn.model_selection import StratifiedKFold 
from sklearn.externals.six.moves import xrange 
# from sklearn.mixture import GMM 
from sklearn import mixture
 
GMM = mixture.GaussianMixture
#生成随机观测点，含有2个聚集核心
obs = np.concatenate((np.random.randn(100, 1), 10 + np.random.randn(300, 1)))
clf = GMM(n_components=2)
print(obs[:10])
clf.fit(obs)
#预测
print(clf.predict([[0], [2], [9], [10]]))