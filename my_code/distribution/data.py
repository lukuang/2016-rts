"""
get some necessary data
"""

import collections
import os

DocScorePair  = collections.namedtuple('DocScorePair', ['scores', 'docids'])

class Run(object):
    """class to store information of a run
    """
    def __init__(self,file_name,N=None):
        self.ranking = {}
        with open(file_name) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                docid = parts[2]
                score = float(parts[4])
                self._distribution_method = parts[5]

                if qid not in self.ranking:
                    self.ranking[qid] = DocScorePair(
                                            scores=[],
                                            docids=[])
                self.ranking[qid].scores.append(score)
                self.ranking[qid].docids.append(docid)
        if N is not None:
            if isinstance(N,int):
                self.ranking[qid].scores = self.ranking[qid].scores[:N]
                self.ranking[qid].docids = self.ranking[qid].docids[:N]
            else:
                raise TypeError("N with type %s" %(type(N)))


class IndexStats(object):
    """class to read index stats(cf,df,n)
    previously generated for query words
    """
    def __init__(self,stat_dir):
        n_file = os.path.join(stat_dir,"n")
        df_file = os.path.join(stat_dir,"df")
        cf_file = os.path.join(stat_dir,"cf")
        self.n = 0
        self.cf = {}
        self.df = {}

        with open(n_file) as f:
            content = f.read()
            content = content.rstrip()
            self.n = int(content)

        with open(df_file) as f:
            for line in f:
                line = line.rstrip()
                if len(line) == 0:
                    continue
                parts = line.split()
                self.df[parts[0]] = float(parts[1])

        self.idf = {}
        for w in self.df:
            self.idf = self.df[w]/(self.n*1.0)

        with open(cf_file) as f:
            for line in f:
                line = line.rstrip()
                if len(line) == 0:
                    continue
                parts = line.split()
                self.cf[parts[0]] = float(parts[1])

class Qrel(object):
    """class to store qrel info
    """
    
    def __init__(self, qrel_file):
        self._judgement = {}
        with open(qrel_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                docid = parts[2]
                jud = parts[3]
                jud = (jud != "0")
                if qid not in self._judgement:
                    self._judgement[qid] = {}
                self._judgement[qid][docid] = jud   
                
    def is_relevant(self,qid,docid):
        return  self._judgement[qid][docid]
                