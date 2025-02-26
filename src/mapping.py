
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
from itertools import product
import re

def norm_string(s):
    """Remove punctuation and lowercasing"""
    s = s.lower().replace('&','and')
    s = re.sub(r'[^\w\d\s]','',s)
    return s

class CompanyMap:
    def __init__(self, name_cols=['NAME','DBA'], addr_col = 'ADDRESS', fuzzy_alg='ratio'):
        self.name_cols = name_cols
        self.addr_col = addr_col
        self.cols = name_cols + [addr_col]

        FUZZY_DICT = {
            'ratio': fuzz.ratio,
            'partial_ratio': fuzz.partial_ratio,
            'token_sort_ratio': fuzz.token_sort_ratio,
            'token_set_ratio': fuzz.token_set_ratio
        }
        try:
            self.fuzzy_alg = FUZZY_DICT[fuzzy_alg]
        except KeyError:
            raise ValueError(f'Invalid fuzzy algorithm: {fuzzy_alg}. Must be one of {list(FUZZY_DICT.keys())}')
    
    def _fuzzycorr(self, X, Y):
        # make sure columns are same
        corr = np.zeros((len(X), len(Y)))
        for i,j in product(range(corr.shape[0]),range(corr.shape[1])):
            scores = []
            scores.append(max([
                self.fuzzy_alg(X.iloc[i][c1], Y.iloc[j][c2]) 
                for c1,c2 in product(self.name_cols,self.name_cols)
                if all([X.iloc[i][c1], Y.iloc[j][c2]])
            ]))
            if all([X.iloc[i][self.addr_col], Y.iloc[j][self.addr_col]]):
                scores.append(self.fuzzy_alg(X.iloc[i][self.addr_col], Y.iloc[j][self.addr_col]))
            corr[i,j] = np.mean(scores)
        return corr

    def fit(self, X):
        
        X = X[self.cols]
        X = X.fillna('')

        for c in self.cols:
            X[c] = X[c].apply(lambda x: norm_string(x))

        self.learned_data = X.drop_duplicates()
        self.matrix = self._fuzzycorr(self.learned_data,self.learned_data)
        
    def match(self, X, threshold=80):

        X = X[self.cols].reset_index(drop=True)
        X = X.fillna('')
        for c in self.cols:
            X[c] = X[c].apply(lambda x: norm_string(x))

        mat = self._fuzzycorr(X, self.learned_data)
        idx = np.argwhere(mat >= threshold)

        similar = np.tril(self.matrix,k=-1)
        similar = similar[idx[:,1]]
        sim_idx = np.argwhere(similar >= threshold)
        similar = np.concatenate([
            np.vstack(X.index[idx[sim_idx[:,0]][:,0]]),
            np.vstack(sim_idx[:,1])
        ],axis=1)
        similar = np.concatenate([idx, similar],axis=0)

        results = pd.DataFrame(similar, columns=['source_idx','match_indices']).drop_duplicates()
        results = results.groupby('source_idx').agg(list).reset_index()

        return results['match_indices']
    