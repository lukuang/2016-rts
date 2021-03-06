"""
score distributions for ranking lists
"""
from __future__ import division
import math
from abc import ABCMeta,abstractmethod
from scipy.stats import gamma,lognorm
from misc import compute_stat_from_list,compute_idf_avg,compute_scq_avg  




class SD(object):
    """base class of 
    score distribution for rankings
    """
    __metaclass__ = ABCMeta
    def __init__(self,run,distribution_method,debug=False):
        self._run,self._distribution_method,self._debug =\
                        run, distribution_method, debug
        self._m1 = {}
        self._v1 = {}
        self._m0 = {}
        self._v0 = {}
        self._lambda = {}
        self._aupr = {}
        self._non_rel_distribution = {}
        self._rel_distribution = {}

    def _estimate_stats_without_rel_info(self,index_stats,queries):
        """estimate the statistics of relevant/non-relevant
        distributions(mean/variance: m/v). Note that the subscripts
        "1,0" corresponds statistics of relevant/non-relevant
        """
        

        self._lambda = {
            "lambda1" :{},
            "lambda2" :{},
            "lambda3" :{}
        }
        for qid in self._run.ranking:
            
            m1,v1,m0,v0 = self._compute_mean_and_var_without_rel_info(qid)

            lambda1,lambda2,lambda3 =\
                self._compute_lambda_without_rel_info(qid,queries,index_stats)
            

            self._m1[qid] = m1
            self._v1[qid] = v1
            self._m0[qid] = m0
            self._v0[qid] = v0
            self._lambda["lambda1"][qid] = lambda1
            self._lambda["lambda2"][qid] = lambda2
            self._lambda["lambda3"][qid] = lambda3
            if self._debug :
                print "for query %s:" %(qid)
                print "m1: %f, v1: %f, m0: %f, v0: %f" %(m1,v1,m0,v0)
                print "lambda1: %f, lambda2: %f, lambda2: %f" %(lambda1,lambda2,lambda3)


    def _estimate_stats_with_rel_info(self,index_stats,queries,qrel):
        """estimate the statistics of relevant/non-relevant
        distributions(mean/variance: m/v). Note that the subscripts
        "1,0" corresponds statistics of relevant/non-relevant
        """

        self._lambda["lambda"] = {}

        for qid in self._run.ranking:
            non_rel = []
            rel = []
            for i in range(len(self._run.ranking[qid].docids)):
                docid = self._run.ranking[qid].docids[i]
                score = self._run.ranking[qid].scores[i]
                if qrel.is_relevant(qid,docid):
                    rel.append(score)
                else:
                    non_rel.append(score)
            m1,v1 = compute_stat_from_list(rel)  
            m0,v0 = compute_stat_from_list(non_rel)
            estimated_lambda = len(rel)*1.0/len(self._run.ranking[qid].docids)


            self._m1[qid] = m1
            self._v1[qid] = v1
            self._m0[qid] = m0
            self._v0[qid] = v0
            self._lambda["lambda"][qid] = estimated_lambda

            if self._debug :
                print "for query %s:" %(qid)
                print "m1: %f, v1: %f, m0: %f, v0: %f" %(m1,v1,m0,v0)
                print "lambda: %f" %(estimated_lambda)
             



    @abstractmethod
    def estimate_distribution(self,index_stats,queries,qrel=None):
        pass

    def _compute_lambda_without_rel_info(self,qid,queries,index_stats):

        lambda1 = 10.0/len(self._run.ranking[qid].scores)
        if lambda1 > 1.0:
            lambda1 = 1.0

        idf_avg = compute_idf_avg(index_stats,queries[qid])
        lambda2 = idf_avg * lambda1
        if lambda2 > 1.0:
            lambda2 = 1.0

        scq_avg = compute_scq_avg(index_stats,queries[qid])
        lambda3 = scq_avg * lambda1
        if lambda3 > 1.0:
            lambda3 = 1.0

        return lambda1,lambda2,lambda3



    def _compute_mean_and_var_without_rel_info(self,qid):
        m1 = .0
        v1 = .0
        m0 = .0
        v0 = .0
        # m1 = 4* stdv(s_max,s_max/2)
        sub_scores = []
        s_max = self._run.ranking[qid].scores[0]
        lower_bound = s_max/2.0
        for score in self._run.ranking[qid].scores:
            if score >= lower_bound:
                sub_scores.append(score)
        temp_mean, temp_var =  compute_stat_from_list(sub_scores)
        m1 = 4*math.sqrt(temp_var)
        m0, v0 = compute_stat_from_list(self._run.ranking[qid].scores)
        if self._distribution_method == "lognormal":
            v1 = ( (m1/m0) * math.sqrt(v0) )**2
        elif self._distribution_method == "gamma":
            v1 = (m1/m0) * v0
        else:
            raise ValueError("The distribution method %s is not supported!" %(_distribution_method))
        return m1,v1,m0,v0


    def _compute_re_likelihood(self,qid,score):
        return self._rel_distribution[qid].pdf(score)

    
    def _compute_non_re_likelihood(self,qid,score):
        return self._non_rel_distribution[qid].pdf(score)

    def _compute_recall(self,qid,score):
        return 1-self._rel_distribution[qid].cdf(score)

    def _compute_fallout(self,qid,score):
        return 1-self._non_rel_distribution[qid].cdf(score)

    def _compute_aupr(self,qid,lambda_value):
        N = len(self._run.ranking[qid].scores)
        ap = .0
        s1 = self._run.ranking[qid].scores[0]
        if self._debug:
            print "for query %s, top score is %f" %(qid,s1)
        score = 2*s1
        recall = 0
        fallout = 0
        prec = [0]*N
        rec = [0]*N
        ds = score/N
        for i in range(N):
            score = score - ds
            #recall += self._compute_re_likelihood(qid,score)*ds
            #fallout += self._compute_non_re_likelihood(qid,score)*ds
            recall = self._compute_recall(qid,score)
            fallout = self._compute_fallout(qid,score)
            #if qid == "429":
            #    print "recall %f" %recall
            #    print "fallot %f" %fallout
            denominator = lambda_value*recall + (1-lambda_value)*fallout
            if recall == 0:
                prec[i] = 0
            else:
                prec[i] = (lambda_value*recall)/denominator
            rec[i] = recall
            if i>0:
                ap += (rec[i]-rec[i-1]) * (prec[i]+prec[i-1])/2
        if self._debug:
            print "ap is %f for query %s" %(ap,qid)

        return ap           


    def predict_aupr(self):
        for lambda_string in self._lambda:
            self._aupr[lambda_string] = {}
            if self._debug:
                print "when using %s" %(lambda_string)
            for qid in self._run.ranking:
    
                lambda_value = self._lambda[lambda_string][qid]
                self._aupr[lambda_string][qid] = \
                        self._compute_aupr(qid,lambda_value)

    @property
    def aupr(self):
        if not self._aupr:
            raise RuntimeError("Parameters are not estimated!")
        else:
            
            return self._aupr


    def show_aupr(self):
        print "-"*20
        print "show aupr estimation"
        for lambda_choice in self._aupr:
            print "\tfor %s" %lambda_choice
            for qid in self._aupr[lambda_choice]:
                print "\t\t%s:%f" %(qid,self._aupr[lambda_choice][qid])
        print "-"*20

    


class GammaSD(SD):
    def __init__(self,run,debug=False):
        super(GammaSD,self).__init__(run,"gamma",debug)


    def _estimate_para(self,index_stats,queries,qrel=None):
        #estimate parameters for models
        if qrel is None:
            self._estimate_stats_without_rel_info(index_stats,queries)
        else:
            self._estimate_stats_with_rel_info(index_stats,queries,qrel)

        self._k1 = {}
        self._theta1 = {}
        self._k0 = {}
        self._theta0 = {}
        for qid in self._run.ranking:
            m1 = self._m1[qid]
            v1 = self._v1[qid]
            m0 = self._m0[qid]
            v0 = self._v0[qid]

            self._k1[qid] = (m1)**2 / v1

            self._theta1[qid] = v1 / m1
            
            self._k0[qid] = (m0)**2 / v0
            self._theta0[qid] = v0 / m0
            if self._debug :
                print "for query %s:" %(qid)
                print "k1: %f, theta1: %f, k0: %f, theta0: %f" %(self._k1[qid],self._theta1[qid],self._k0[qid],self._theta0[qid])




    def estimate_distribution(self,index_stats,queries,qrel=None):
        self._estimate_para(index_stats,queries,qrel)


        for qid in self._run.ranking:
            self._rel_distribution[qid] = gamma(self._k1[qid],1/self._theta1[qid]) 
            self._non_rel_distribution[qid] = gamma(self._k0[qid],1/self._theta0[qid])  







class LognormalSD(SD):
    def __init__(self,run,debug=False):
        super(LognormalSD,self).__init__(run,"lognormal",debug)

    def _estimate_para(self,index_stats,queries,qrel=None):
        #estimate parameters for models
        if qrel is None:
            self._estimate_stats_without_rel_info(index_stats,queries)
        else:
            self._estimate_stats_with_rel_info(index_stats,queries,qrel)

        self._mu1 = {}
        self._sigma1 = {}
        self._mu0 = {}
        self._sigma0 = {}
        for qid in self._run.ranking:
            m1 = self._m1[qid]
            v1 = self._v1[qid]
            m0 = self._m0[qid]
            v0 = self._v0[qid]

            self._mu1[qid] = math.log(m1) - 0.5*(1 + (v1/(m1**2)) )
            var1 = math.log(1 + (v1/(m1**2)) )
            self._sigma1[qid] = math.sqrt(var1)
            self._mu0[qid] = math.log(m0) - 0.5*(1 + (v0/(m0**2)) )
            var0 = math.log(1 + (v0/(m0**2)) )
            self._sigma0[qid] = math.sqrt(var0)
            if self._debug :
                print "for query %s:" %(qid)
                print "mu1: %f, sigma1: %f, mu0: %f, sigma0: %f" %(self._mu1[qid],self._sigma1[qid],self._mu0[qid],self._sigma0[qid])





    def estimate_distribution(self,index_stats,queries,qrel=None):

        self._estimate_para(index_stats,queries,qrel)


        for qid in self._run.ranking:
            self._rel_distribution[qid] = lognorm(self._sigma1[qid],scale = math.exp(self._mu1[qid])) 
            self._non_rel_distribution[qid] = lognorm(self._sigma0[qid],scale = math.exp(self._mu0[qid]))
