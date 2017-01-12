"""
get some necessary data
"""
from __future__ import division
import collections
import os,re
import json
import math

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
            try:
                self.idf[w] = (self.n*1.0)/self.df[w]
            except ZeroDivisionError:
                self.idf[w] = 0

        with open(cf_file) as f:
            for line in f:
                line = line.rstrip()
                if len(line) == 0:
                    continue
                parts = line.split()
                self.cf[parts[0]] = float(parts[1])


class  T2Day(object):
    """store t2day mapping for tweets 
    """
    def __init__(self,t2day_file):
        self._t2day_file = t2day_file

        self._read_t2day_file()


    def _read_t2day_file(self):
        self._t2day_map = {}
        self._t2epoch_map = {}
        with open(self._t2day_file) as f:
            for line in f:
                parts = line.split()
                tid = parts[0]
                day_info = parts[1] 
                epoch_sec = parts[2] 
                m = re.match("201507(\d+)",day_info)
                if m:
                    date = m.group(1)
                    self._t2day_map[tid] = date
                    self._t2epoch_map[tid] = epoch_sec
                else:
                    raise RuntimeError("mal t2day file line:\n%s",line)

    def get_date(self,tid):
        try:
            return self._t2day_map[tid]
        except KeyError:
            return None

    def get_epoch(self,tid):
        try:
            return self._t2epoch_map[tid]
        except KeyError:
            return None


class SemaCluster(object):
    """store semantic cluster
    """
    def __init__(self,cluster_file,t2day,is_16=False):
        self._cluster_file = cluster_file
        if not is_16:
            self._read_cluster_file_15(t2day)
        else:
            self._read_cluster_file_16(t2day)



    def _read_cluster_file_15(self,t2day):
        self._cluster = {}
        self._day_cluster = {}
        all_data = json.load(open(self._cluster_file))["topics"]
        for qid in all_data:
            self._cluster[qid] = {}
            for i in range(len(all_data[qid]["clusters"])):
                cluster_id = i
                self._cluster[qid][cluster_id] = all_data[qid]["clusters"][i]
                
                for tid in all_data[qid]["clusters"][i]:
                    date = t2day.get_date(tid)
                    if date not in self._day_cluster:
                        self._day_cluster[date] = {}
                    if qid not in self._day_cluster[date]:
                        self._day_cluster[date][qid] = {}
                    if cluster_id not in self._day_cluster[date][qid]:
                        self._day_cluster[date][qid][cluster_id] = []

                    self._day_cluster[date][qid][cluster_id].append(tid)

    def _read_cluster_file_16(self,t2day):
        self._cluster = {}
        self._day_cluster = {}
        all_data = json.load(open(self._cluster_file))["topics"]
        for qid in all_data:
            self._cluster[qid] = {}
            for cluster_id in all_data[qid]["clusters"]:
                self._cluster[qid][cluster_id] = all_data[qid]["clusters"][cluster_id]
                
                for tid in all_data[qid]["clusters"][cluster_id]:
                    date = t2day.get_date(tid)
                    if date not in self._day_cluster:
                        self._day_cluster[date] = {}
                    if qid not in self._day_cluster[date]:
                        self._day_cluster[date][qid] = {}
                    if cluster_id not in self._day_cluster[date][qid]:
                        self._day_cluster[date][qid][cluster_id] = []

                    self._day_cluster[date][qid][cluster_id].append(tid)



    @property
    def cluster(self):
        return self._cluster

    @property
    def day_cluster(self):
        return self._day_cluster
    
    

    def cluster_4_day_qid(self,day,qid):
        """return a list of cluster_ids that occur
        in this day for the qid
        """
        try:
            return self._day_cluster[day][qid].keys()
        except KeyError:
            return []

    def same_cluster(self,qid,docid1,docid2):
        for cluster_id in self._cluster[qid]:
            cluster = self._cluster[qid][cluster_id]
            #print cluster,docid1,docid2
            if (docid1 in cluster) and (docid2 in cluster):
                return True
        return False

    def all_cluster_recall(self,results):
        return self._compute_cluster_precision(
                        results,self._cluster)

    def day_cluster_recall(self,results,date):
        return self._compute_cluster_recall(
                        results,self._day_cluster[date])

    def get_cluster_id(self,qid,tid):
        for cluster_id in self._cluster[qid]:
            if tid in self._cluster[qid][cluster_id]:
                return cluster_id
        return None

    def _compute_cluster_recall(self,results,cluster_info):
        cluster_covered = {}
        cluster_recall = .0
        for qid in results:
            # if not cluster for this query, skip it
            if qid not in cluster_info:
                continue
            if qid not in cluster_covered:
                cluster_covered[qid] = set()
            for tid in results[qid]:
                #print "for tid: %s" %tid
                for cluster_id in cluster_info[qid]:
                    if  tid in cluster_info[qid][cluster_id]:
                        #print "found tid in cluster %s" %cluster_id
                        cluster_covered[qid].add(cluster_id)
            try:
                cluster_recall += len(cluster_covered[qid])*1.0/len(cluster_info[qid])
            except ZeroDivisionError:
                pass

        return cluster_recall*1.0/len(results)

    


class Qrel(object):
    """class to store qrel info
    """
    
    def __init__(self, qrel_file):
        self._judgement = {}
        self._qids = []
        self._days = []
        for i in range(20,30):
            self._days.append(str(i))

        self._qrels_dt = {}
        with open(qrel_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                docid = parts[2]
                score = int(parts[3])
                if score == -1:
                    score = 0
                else:
                    if score == 3:
                        score = 1
                    elif score ==4:
                        score = 2

                jud = (score != 0)
                if qid not in self._judgement:
                    self._judgement[qid] = {}
                    self._qrels_dt[qid] = {}
                    self._qids.append(qid)
                self._judgement[qid][docid] = jud
                self._qrels_dt[qid][docid] = score*1.0/2
    
    def num_of_relevant(qid):
        return len(self._judgement[qid])

    def is_relevant(self,qid,docid):
        try:
            return  self._judgement[qid][docid]
        except KeyError:
            return False

    def precision(self,results):
        return self._compute_performance(results,"precision")

    def recall(self,results):
        return self._compute_performance(results,"recall")

    def f1(self,results):
        return self._compute_performance(results,"f1")


    def ndcg10(self,results,sema_cluster):
        existed_clusters = {}
        total_score = .0
        for day in self._days:
            if day in results:
                day_results = results[day]
            else:
                day_results = {}
            total_score += self.day_dcg10(day,day_results,existed_clusters,sema_cluster)

        return total_score *1.0/ len(self._days)


    def day_dcg10_no_pre(self,day,day_results,sema_cluster):
        #compute day ndcg while not considering results retrieved
        #previously
        existed_clusters = {}
        return self.day_dcg10(day,day_results,existed_clusters,sema_cluster)

    def raw_ndcg10(self,day,day_results,sema_cluster):
        limit = 10
        result_size = {}
        total_score = .0
        for qid in day_results:
        
            
            top_gains = []
            if qid in sema_cluster.day_cluster[day]:
                for cluster_id in sema_cluster.day_cluster[day][qid]:
                    for tid in sema_cluster.day_cluster[day][qid][cluster_id]:
                        top_gains.append(self._qrels_dt[qid][tid])
    
            ndcg = .0
            gains = []
            result_size[qid] = 0
            for tid in day_results[qid]:
                if result_size[qid] == limit:
                    break
                gain = .0
                cluster_id = sema_cluster.get_cluster_id(qid,tid)
                if cluster_id is not None:
                    gain = self._qrels_dt[qid][tid]
                    
                gains.append(gain)
                result_size[qid] += 1

            dcg = .0
            for i in range(len(gains)):
                gain  = gains[i]
                dcg += (pow(2, gain) - 1) * 1.0 / math.log(i + 2, 2)

            
            top_gains.sort(reverse = True)
            rank_cut = min(len(top_gains), limit)
            idcg = 0.0
            top_gains = top_gains[:rank_cut]
            for i in range(rank_cut):
                gain = top_gains[i]
                idcg = idcg + (pow(2, gain) - 1) * 1.0 / math.log(i + 2, 2)
            
            if idcg != 0:
                ndcg = dcg / idcg
            total_score += ndcg
            
           

        total_score = total_score*1.0/len(day_results)
        #if total_score!=0:
        #    print "return %f" %total_score
        return total_score

    def day_dcg10(self,day,day_results,existed_clusters,sema_cluster):
        limit = 10
        result_size = {}
        total_score = .0
        for qid in day_results:
            if qid not in existed_clusters:
                existed_clusters[qid] = set()
            interesting = False
            
            max_gain_dt = {}
            if qid in sema_cluster.day_cluster[day]:
                for cluster_id in sema_cluster.day_cluster[day][qid]:
                    if cluster_id not in existed_clusters[qid]:
                        interesting = True
                        max_gain_dt[cluster_id] = .0
                        for tid in sema_cluster.day_cluster[day][qid][cluster_id]:
                            max_gain_dt[cluster_id] = max(max_gain_dt[cluster_id],self._qrels_dt[qid][tid])
    
            if interesting:
                if qid in day_results:
                    ndcg = .0
                    gains = []
                    result_size[qid] = 0
                    for tid in day_results[qid]:
                        if result_size[qid] == limit:
                            break
                        gain = 0
                        cluster_id = sema_cluster.get_cluster_id(qid,tid)
                        if cluster_id is not None:
                            if cluster_id not in existed_clusters[qid]:
                                existed_clusters[qid].add(cluster_id)
                                gain = self._qrels_dt[qid][tid]
                                if cluster_id in max_gain_dt:
                                    gain = max_gain_dt[cluster_id]
                        #print "add gain %f for tid %s cid %s" %(gain,tid,cluster_id)
                        gains.append(gain)
                        result_size[qid] += 1
                    dcg = .0
                    for i in range(len(gains)):
                        gain  = gains[i]
                        dcg += (pow(2, gain) - 1) * 1.0 / math.log(i + 2, 2)

                    top_gains = max_gain_dt.values()
                    top_gains.sort(reverse = True)
                    rank_cut = min(len(top_gains), limit)
                    idcg = 0.0
                    top_gains = top_gains[:rank_cut]
                    for i in range(rank_cut):
                        gain = top_gains[i]
                        idcg = idcg + (pow(2, gain) - 1) * 1.0 / math.log(i + 2, 2)
                    
                    if idcg != 0:
                        ndcg = dcg / idcg
                    total_score += ndcg
            
            else:
                if qid not in day_results or len(day_results[qid]) == 0:
                    total_score += 1

        total_score = total_score*1.0/len(day_results)
        #if total_score!=0:
        #    print "return %f" %total_score
        return total_score

    def check_redundant_day(self,qid,day,existed_clusters,sema_cluster):
        """check whether a days is a redundant day
        based on the existed_clusters and semantic 
        cluster information
        """
        if qid not in sema_cluster.day_cluster[day]:
            # if it is a silent day, it is not a redundant day
            return False
        else:
            # if there is any cluster not covered previously,
            # it is not a redundant day. Set interesting to True
            for cluster_id in sema_cluster.day_cluster[day][qid]:
                if cluster_id not in existed_clusters[qid]:
                    return True

            return False




    def get_redundant_days(self,results,sema_cluster):
        """get redundant day based on whether the
        clusters in a day of a topic is covered 
        by the result of previous dat
        """
        limit = 10
        result_size = {}
        redundant_days = {}
        existed_clusters = {}
        for day in results:
            for qid in results[day]:
                if qid not in existed_clusters:
                    existed_clusters[qid] = set()
                    redundant_days[qid] = set()

                interesting = False
                
                if qid not in sema_cluster.day_cluster[day]:
                    # if it is a silent day, it is not a redundant day
                    continue
                else:
                    # if there is any cluster not covered previously,
                    # it is not a redundant day. Set interesting to True
                    for cluster_id in sema_cluster.day_cluster[day][qid]:
                        if cluster_id not in existed_clusters[qid]:
                            interesting = True
                            break

                    if not interesting:
                        redundant_days[qid].add(day)

                    else:
                        # update existed_clusters from results
                        result_size[qid] = 0
                        for tid in results[day]:
                            if result_size[qid] == limit:
                                break
                            cluster_id = sema_cluster.get_cluster_id(qid,tid)
                            if cluster_id is not None:
                                if cluster_id not in existed_clusters[qid]:
                                    existed_clusters[qid].add(cluster_id)
                    
                            result_size[qid] += 1

        return redundant_days
                            

    def get_irrelevant_days(self,results,sema_cluster):
        """get all irrelevant days depending on
        whether there are relevant tweets on the
        day
        """
        limit = 10
        irrelevant_days = {}
        for day in sema_cluster.day_cluster:
            for qid in sema_cluster.cluster:
                if qid not in irrelevant_days:
                    irrelevant_days[qid] = set()

                
                if qid not in sema_cluster.day_cluster[day]:
                    irrelevant_days[qid].add(day)

        return irrelevant_days



    def _compute_performance(self,results,method):
        performance = .0
        for qid in results:
            num_of_rel = 0
            for docid in results[qid]:
                if self.is_relevant(qid,docid):
                    num_of_rel += 1

            q_result_size = len(results[qid])
            try:
                if method == "precision":
                    performance += num_of_rel*1.0/q_result_size
                elif method == "recall":
                    query_rel_num = 0
                    for judge in self._judgement[qid].values():
                        if judge:
                            query_rel_num += 1
                    performance += num_of_rel*1.0/query_rel_num
                  
                elif method == "f1":
                    query_rel_num = 0
                    for judge in self._judgement[qid].values():
                        if judge:
                            query_rel_num += 1

                    q_percision = num_of_rel*1.0/q_result_size
                    q_recall = num_of_rel*1.0/query_rel_num
                    f1 = 2.0*q_percision*q_recall/(q_percision+q_recall)
                    performance += f1

            except ZeroDivisionError:
                performance += .0

        num_of_q = len(results)

        return performance*1.0/num_of_q


    @property
    def qids(self):
        return self._qids
    
                