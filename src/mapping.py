
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
import re

def norm_string(s):
    """Remove punctuation and lowercasing"""
    if isinstance(s,str):
        s = s.lower().replace('&','and')
        s = re.sub(r'[^\w\d\s]','',s)
        return s
    return ''

class CompanyMap:
    def __init__(self, target_data, name_cols=['NAME','DBA'], addr_col = 'ADDRESS', fuzzy_alg='ratio'):
        self._set_target(target_data,name_cols,addr_col)

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
    
    def _score(self, x, y):
        if (len(x)>0) & (len(y)>0):
            return self.fuzzy_alg(x,y)
        return np.nan

    def _set_target(self, X, name_cols, addr_col):

        for c in name_cols + [addr_col]:
            X['norm_'+c] = X[c].apply(lambda x: norm_string(x))

        self.name_cols = ['norm_'+n for n in name_cols]
        self.addr_col = 'norm_'+addr_col
        self.cols = self.name_cols + [self.addr_col]

        self.learned_data = X
        
    def get_match_idx(self, names = [], address = '', threshold=95, avg_threshold=80):

        names = [norm_string(n) for n in names]
        address = norm_string(address)

        namescore = []
        for n in names:
            for c in self.name_cols:
                namescore.append(np.vstack(self.learned_data[c].apply(lambda x: self._score(x, n)).values))
        namescore = np.nanmax(np.concatenate(namescore,axis=1),axis=1)

        addrscore = self.learned_data[self.addr_col].apply(lambda x: self._score(x, address))

        score = np.nanmean([namescore, addrscore],axis=0)

        return list(self.learned_data[(score >= avg_threshold) & ((namescore >= threshold) | (addrscore >= threshold))].index)
    
    def get_match_df(self, names = [], address = '', threshold=95, avg_threshold=80):
        idx = self.get_match_idx(names, address, threshold, avg_threshold)
        return self.learned_data.iloc[idx]
    
def fuzzy_join(
        left_df, 
        right_df, 
        name_cols, 
        addr_col, 
        how='left', 
        threshold=95, 
        avg_threshold=80, 
        fuzzy_alg='ratio',
    ):
    c = CompanyMap(right_df, name_cols, addr_col, fuzzy_alg)
    matches = left_df.apply(lambda x: c.get_match_idx(x[name_cols], x[addr_col], threshold, avg_threshold), axis=1)
    df = pd.concat([left_df, pd.DataFrame(matches.tolist())],axis=1).melt(id_vars=left_df.columns)
    df = df.set_index('value',drop=False).join(c.learned_data,lsuffix='_l',rsuffix='_r',how=how)
    return df
    