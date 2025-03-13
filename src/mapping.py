
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
import re
from tqdm.auto import tqdm

tqdm.pandas()

def norm_string(s):
    """Remove punctuation and lowercasing"""
    if isinstance(s,str):
        s = s.lower().replace('&','and')
        s = re.sub(r'[^\w\d\s]','',s)
        s = re.sub(r'\s+',' ',s)
        return s
    return ''

class Mapper:
    def __init__(self, target_data, name_cols, addr_col):
        self.learned_data = target_data.reset_index(drop=True)
        self.name_cols = name_cols
        self.addr_col = addr_col

    def _score(self, x, y, fuzzy_alg):
        if (len(x)>0) & (len(y)>0):
            return fuzzy_alg(x,y)
        return np.nan

    def get_match_idx(self, names = [], address = '', threshold=95, avg_threshold=80, fuzzy_alg=fuzz.ratio):

        names = [norm_string(n) for n in names]
        address = norm_string(address)

        namescore = []
        for n in names:
            for c in self.name_cols:
                namescore.append(np.vstack(self.learned_data[c].apply(lambda x: self._score(x, n, fuzzy_alg)).values))
        namescore = np.nanmax(np.concatenate(namescore,axis=1),axis=1)

        addrscore = self.learned_data[self.addr_col].apply(lambda x: self._score(x, address, fuzzy_alg))

        score = np.nanmean([namescore, addrscore],axis=0)

        return list(self.learned_data[
            (score>=avg_threshold) & ((namescore>=threshold)|(addrscore>=threshold))
        ].index)
    
    def get_match_df(self, names = [], address = '', threshold=95, avg_threshold=80, fuzzy_alg=fuzz.ratio):
        idx = self.get_match_idx(names, address, threshold, avg_threshold, fuzzy_alg)
        return self.learned_data.iloc[idx]


class CompanyMap(Mapper):
    def __init__(self, target_data, name_cols=['NAME','DBA'], addr_col = 'ADDRESS', ref_name='NoName'):
        super(CompanyMap, self).__init__(
            *self._set_targets(target_data,name_cols,addr_col)
        )
        self.ref_name = ref_name

    def _set_targets(self, X, name_cols, addr_col):

        names = []
        for i,c in enumerate(name_cols):
            names.append(f'norm_NAME{i}')
            X[names[-1]] = X[c].apply(lambda x: norm_string(x))
        X['norm_ADDRESS'] = X[addr_col].apply(lambda x: norm_string(x))

        addr = 'norm_ADDRESS'

        return X, names, addr
    
def fuzzy_join(
        left_df, 
        left_name_cols,
        left_addr_col,
        right_df, 
        right_name_cols,
        right_addr_col, 
        how='left',
        threshold=95, 
        avg_threshold=80,
    ):
    c = CompanyMap(right_df, right_name_cols, right_addr_col)
    matches = left_df.progress_apply(lambda x: c.get_match_idx(x[left_name_cols], x[left_addr_col], threshold, avg_threshold), axis=1)
    df = pd.concat([left_df, pd.DataFrame(matches.tolist())],axis=1).melt(id_vars=left_df.columns)
    df = df.set_index('value',drop=False).join(c.learned_data,lsuffix='_l',rsuffix='_r',how=how)
    return df
    

class OneMapToRuleThemAll(Mapper):

    def __init__(self, mappers, threshold=95, avg_threshold=80):
        self.mappers = {m.ref_name:m for m in mappers}
        self.threshold=threshold
        self.avg_threshold = avg_threshold

        super(OneMapToRuleThemAll, self).__init__(
            *self._concat_data()
        )

        self.learned_data['internal_match'] = self._internal_matches(self.learned_data)

    def _concat_data(self):
        df = pd.concat([
            m.learned_data[m.name_cols + [m.addr_col]].assign(keys=list(zip([k]*len(m.learned_data),m.learned_data.index)))
            for k,m in self.mappers.items()
        ],axis=0).fillna('')

        names = [c for c in df.columns if c.startswith('norm_NAME')]
        addr = 'norm_ADDRESS'

        df = df.groupby(names + [addr]).agg({'keys':list}).reset_index()

        return df, names, addr
    
    def _internal_matches(self, df):
        return df.progress_apply(
            lambda x: self.get_match_idx(
                x[self.name_cols], 
                x[self.addr_col],
                self.threshold, 
                self.avg_threshold
            ), axis=1
        )


    def get_matches(self, names = [], address = '', threshold=95, avg_threshold=80):
        matches = self.get_match_df(names, address, threshold, avg_threshold, fuzzy_alg=fuzz.partial_ratio)['internal_match']
        results = {}
        for map_id, idx in pd.DataFrame((self.learned_data.iloc[matches.values.sum()]['keys'].values).sum()).groupby(0):
            results[map_id] = self.mappers[map_id].learned_data.iloc[idx[1].values]
        return results
