
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
from itertools import product

def clean_names(names):
    """Clean names by removing punctuation and lowercasing"""
    # lower case
    # turn ampersand to "and"
    # shorten anything "incorporated" should be inc
    # "limited liability company" to llc?
    # other company specific weirdnesses?
    # then, remove all other punct
    pass

def clean_addresses(addresses):
    # lower case
    # how to parse and normalize? based on punct, state abbreve? or just keep whole string and do general cleanup?
    pass


class CompanyMap:
    def __init__(self, name_cols=['NAME','DBA'], addr_col = 'ADDRESS', fuzzy_kwargs={}):
        self.fuzzy_kwargs = fuzzy_kwargs
        self.name_cols = name_cols
        self.addr_col = addr_col
    
    def _fuzzycorr(self, X, Y):
        # make sure columns are same
        corr = np.zeros((len(X), len(Y)))
        for i,j in product(range(corr.shape[0]),range(corr.shape[1])):
            scores = []
            scores.append(max([
                fuzz.ratio(X.iloc[i][c1], Y.iloc[j][c2]) 
                for c1,c2 in product(self.name_cols,self.name_cols)
                if all([X.iloc[i][c1], Y.iloc[j][c2]])
            ]))
            if all([X.iloc[i][self.addr_col], Y.iloc[j][self.addr_col]]):
                scores.append(fuzz.ratio(X.iloc[i][self.addr_col], Y.iloc[j][self.addr_col]))
            corr[i,j] = np.mean(scores)
        return corr

    def fit(self, X):
        """X should contain SOURCE, NAME, DBA, and ADDRESS"""
        """what to do about original dataset ids?"""
        #X['NAME'] = clean_names(X['NAME'])
        #X['DBA'] = clean_names(X['DBA'])
        #X['ADDRESS'] = clean_addresses(X['ADDRESS'])
        X = X[self.name_cols+[self.addr_col]].fillna('')
        self.learned_data = X.drop_duplicates()
        self.matrix = self._fuzzycorr(self.learned_data,self.learned_data)
        
    def match(self, X, threshold=80):
        #X['CLEAN_NAME'] = clean_names(X['NAME'])
        #X['CLEAN_DBA'] = clean_names(X['DBA'])
        #X['CLEAN_ADDRESS'] = clean_addresses(X['ADDRESS'])
        X = X[self.name_cols+[self.addr_col]].fillna('')
        X.reset_index(drop=True, inplace=True)

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
        

# use this to then base full contractor list on registry (if does not exist in registry, prioritize which to use)
# exists in registry flag
# only join if score is > ?
# if multiple matches, how to handle
# how to evaluate matching