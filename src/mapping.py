
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

class FuzzyMatch:

    def __init__(
        self,
        name_cols,
        addr_col,
        threshold=95,
        avg_threshold=80,
        fuzzy_alg=fuzz.ratio,
    ):
        self.name_cols = name_cols
        self.addr_col = addr_col
        self.threshold = threshold
        self.avg_threshold = avg_threshold
        self.fuzzy_alg = fuzzy_alg

    def _score(self, x, y):
        if (len(x)>0) & (len(y)>0):
            return self.fuzzy_alg(x,y)
        return np.nan

    def _get_match_idx(self, names = [], address = ''):

        namescore = []
        for n in names:
            for c in self.name_cols:
                namescore.append(np.vstack(self.name_df[c].apply(lambda x: self._score(x, n)).values))
        namescore = np.nanmax(np.concatenate(namescore,axis=1),axis=1)

        addrscore = self.name_df[self.addr_col].apply(lambda x: self._score(x, address))

        score = np.nanmean([namescore, addrscore],axis=0)

        return list(self.name_df[
            (score>=self.avg_threshold) & ((namescore>=self.threshold)|(addrscore>=self.threshold))
        ].index)
    
    def _company_indexes(self, df_dict):

        cols = self.name_cols + [self.addr_col]

        for k,v in df_dict.items():
            for col in cols:
                v[col] = v[col].apply(lambda x: norm_string(x))
            df_dict[k] = v

        name_df = pd.concat([v[cols] for v in df_dict.values()])
        name_df = name_df.drop_duplicates().reset_index(drop=True)
        name_df.reset_index(drop=False, inplace=True)
        name_df.rename(columns={'index':'COMPANY_ID'}, inplace=True)

        for k,v in df_dict.items():
            v = v.merge(name_df, how='left', on=cols)
            v.drop(cols, axis=1, inplace=True)
            df_dict[k] = v

        return name_df, df_dict
    
    def index_and_match(self, df_dict):
        self.name_df, df_dict = self._company_indexes(df_dict)
        match_ids = self.name_df.progress_apply(lambda x: self._get_match_idx(
                x[self.name_cols], 
                x[self.addr_col],
            ), axis=1)
        
        match_df = pd.concat([self.name_df['COMPANY_ID'],pd.DataFrame(match_ids.to_list())],axis=1)
        match_df = match_df.melt(id_vars='COMPANY_ID').dropna(subset='value').reset_index(drop=True).drop(columns=['variable'])
        match_df.reset_index(drop=False, inplace=True)
        match_df.rename(columns={'index':'MATCH_ID','value':'COMPANY_MATCH'}, inplace=True)
        
        return match_df.astype(int), df_dict