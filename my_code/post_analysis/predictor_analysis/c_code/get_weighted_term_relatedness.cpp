/* get idf average for query words given index()
*/


#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/Parameters.hpp"
#include "indri/QueryEnvironment.hpp"
#include <dirent.h>
#include <iostream>
#include <string>
#include <sstream>
#include <typeinfo>
#include <algorithm>
#include <map>
#include <math.h>
#include <fstream>
#include <dirent.h>
#include "utility.hpp"
using namespace std;





//get unique index vectors of given size for a range of ints 
vector< vector<int> > get_index_vector(const int& begin,const int& end,const int& size){
    vector< vector<int> > index_vector;
    int range = end-begin+1;
    if(range >= size){
        for(int i = begin; i<= end; i++){
            if(size>1){
                int sub_size = size-1;
                vector< vector<int> > sub_index_vector = get_index_vector(i+1,end,sub_size);
                
                for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                    (*iit).push_back(i);
                    index_vector.push_back(*iit);
                }

                vector< vector<int> > sub_index_vector_full_size = get_index_vector(i+2,end,size);
                for(vector< vector<int> >::iterator iit=sub_index_vector_full_size.begin(); iit!=sub_index_vector_full_size.end();++iit){
                    index_vector.push_back(*iit);
                }
            }
            else{
                std::vector<int> single_word;
                single_word.push_back(i);
                index_vector.push_back(single_word);
            }
        }
    }
    return index_vector;
}

map<string, vector <vector<string> > > get_2words_vector( map<string, vector<string> >& queries ){
    map<string, vector <vector<string> > > query_2words_vector ;
    for(map<string, vector<string> >::iterator it=queries.begin(); it!=queries.end();++it){
        vector< vector<string> > subwords_vector;
        // cout<<"for query "<<it->first<<" add :"<<endl;
        if(it->second.size()>=1){
            
            int end_index = it->second.size()-1;
            int sub_vector_size = 2;
            vector< vector<int> > sub_index_vector = get_index_vector(0,end_index,sub_vector_size); 
            for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                vector<string> temp_word_vector;
                for(std::vector<int>::iterator sit=(*iit).begin(); sit!=(*iit).end();++sit){
                    temp_word_vector.push_back(it->second[*sit]);
                }
                subwords_vector.push_back(temp_word_vector);
                // cout<<"\t";
                // for(int k=0;k<temp_word_vector.size();k++ ){
                //     cout<<" "<<temp_word_vector[k];
                // }
                // cout<<endl;
            }
        
        }
        query_2words_vector[it->first] = subwords_vector;
    }
    return query_2words_vector;
}

int get_collection_size( indri::collection::Repository& r) {
  indri::server::LocalQueryServer local(r);
  return  local.documentCount();
}

float get_log_idf(indri::collection::Repository& r, const int& n,const string& term){
    indri::server::LocalQueryServer local(r);
    int df = local.documentStemCount(term);
    if(df == 0){
        return .0;
    }
    else{
        float idf=(n*1.0)/df;
        return log(idf);
    }
}

vector<int> get_docid_vector_for_term(indri::collection::Repository& r,const string& term){
    vector<int> docids;
    indri::server::LocalQueryServer local(r);
    indri::collection::Repository::index_state state = r.indexes();
    for( size_t i=0; i<state->size(); i++ ) {
        indri::index::Index* index = (*state)[i];
        indri::thread::ScopedLock( index->iteratorLock() );

        indri::index::DocListIterator* iter = index->docListIterator( term );
        if (iter == NULL) continue;

        iter->startIteration();

        int doc = 0;
        indri::index::DocListIterator::DocumentData* entry;

        for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
          entry = iter->currentEntry();

           docids.push_back(entry->document); 
        }

        delete iter;
    }
    return docids;
}

float get_pmi(indri::collection::Repository& r,const string& term1, const string& term2, const int& n){
    vector<int> term_did_1 = get_docid_vector_for_term(r,term1);
    vector<int> term_did_2 = get_docid_vector_for_term(r,term2);
    map<int, int> common_docid;
    if(term_did_1.size() == 0 || term_did_2.size()==0){
        return .0;
    }
    for(vector<int>::iterator it=term_did_1.begin(); it!=term_did_1.end(); ++it){
        if(common_docid.find(*it)==common_docid.end()){
            common_docid[*it] = 0;
        }
    }
    for(vector<int>::iterator it=term_did_2.begin(); it!=term_did_2.end(); ++it){
        if(common_docid.find(*it)==common_docid.end()){
            common_docid[*it] = 0;
        }
    }
    float probability = (n*common_docid.size()*1.0)/(term_did_1.size()*term_did_2.size());
    return log(probability);
}

map<string, map<string, float> >  get_term_relatedness(indri::collection::Repository& r, map<string, vector <vector<string> > > query_2words_vector,const int& n,map<string, vector<string> > queries,map<string, float>& idf){
    map<string, map<string, float> >  term_relatedness;
    for(map<string, vector <vector<string> > >::const_iterator it=query_2words_vector.begin();it!=query_2words_vector.end();++it){
        string qid = it->first;
        map <string,float> one_query_relatedness ;
        if(it->second.size()!=0){
            vector <vector<string> > one_query_2words_vector = it->second;
            for(vector <vector<string> >::const_iterator oit=one_query_2words_vector.begin(); oit!=one_query_2words_vector.end(); ++oit){

                string subquery_string = (*oit)[0] + " " + (*oit)[1];
                one_query_relatedness[subquery_string] = get_pmi(r,(*oit)[0],(*oit)[1],n);
                one_query_relatedness[subquery_string] *= idf[ (*oit)[0] ]*idf[ (*oit)[1] ];
            }
            
        }
        else{
            one_query_relatedness[queries[qid][0]] = get_log_idf(r,n,queries[qid][0]);
        }
        term_relatedness[it->first] = one_query_relatedness;
    }
    return term_relatedness;
}





void show_relatedness( map<string, map<string, float> > term_relatedness,const string& cu){
    float max_value = .0;
    map<string, float> pmi;
    for(map<string, map<string, float> >::iterator it=term_relatedness.begin(); it!=term_relatedness.end();++it){
        float final_value = .0;
        // cout<<"for "<<it->first<<endl;
        for(map<string, float>::iterator rit=it->second.begin();rit!=it->second.end();++rit){
            // cout<<"\tfor "<<rit->first<<" term relatedness is "<<rit->second<<endl;
            if(cu == "max"){
                if(rit->second > final_value){
                    final_value = rit->second;
                }
            }
            else {
                final_value += rit->second;
            }
        }
        if(cu == "average"){
            final_value /= it->second.size()*1.0;
        }
        if (final_value > max_value){
            max_value = final_value;
        }
        pmi[it->first] = final_value;
    }
    
    for(map<string, float>::iterator it=pmi.begin(); it!=pmi.end();++it){
        float final_value = it->second/max_value;
        cout << it->first<<" "<<final_value<<endl;
    }


}





int get_co_occurrence_count(const vector< map<string,int> >& one_result_term_map,const vector<string> & subquery_words){
    int count = 0;
    for(vector< map<string,int> >::const_iterator it=one_result_term_map.begin();it!=one_result_term_map.end();++it){
        map<string,int> doc_term_map = *it;

        int appear_count = 0;
        for(int i=0;i<subquery_words.size();i++){
            if(doc_term_map.find(subquery_words[i])!=doc_term_map.end()){
                appear_count += 1;
            }
        }
        if(appear_count==subquery_words.size()){
            count += 1;
        }
    }
    return count;
}

map<string, vector <int> > get_co_occurrence_map( map<string, vector <vector<string> > >& query_subwords_vector, map<string, vector< map<string,int> > >& result_term_map){
    map<string, vector <int> > co_occurrence_map ;
    for(map<string, vector <vector<string> > >::const_iterator it=query_subwords_vector.begin();it!=query_subwords_vector.end();++it){
        string qid = it->first;
        std::vector<int> co_occurrence_counts;
        vector< map<string,int> > one_result_term_map = result_term_map[qid];
        vector <vector<string> > one_query_subwords_vector = query_subwords_vector[qid];
        for(vector <vector<string> >::const_iterator oit=one_query_subwords_vector.begin(); oit!=one_query_subwords_vector.end(); ++oit){
            int count = get_co_occurrence_count(one_result_term_map,*oit);

            co_occurrence_counts.push_back(count);
        }
        co_occurrence_map[qid] = co_occurrence_counts;
    }
    return co_occurrence_map;
}



void get_statistics(indri::collection::Repository& r,map<string, float>& idf,vector<string>& query_words){

    indri::server::LocalQueryServer local(r);
    float n = 1.0*local.documentCount();
    for(vector<string>::iterator it = query_words.begin(); it!=query_words.end(); ++it){
        int df = local.documentStemCount(*it) ;

        if( df == 0){
            idf[*it] = .0;
        }
        else{
            idf[*it] = log(n/df );        
        }
    }

}


static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query") ) || 
      !( param.exists( "index") ) ||
      !( param.exists( "cu")    ) )  {
   std::cerr << "get_term_relatedness usage: " << std::endl
             << "   get_term_relatedness -query=myquery -index=myindex" << std::endl;
   exit(-1);
  }
  string cu = param[ "cu" ];
  if(  cu!="average" &&
       cu!="max" ){
    std::cerr << "cu must be one of the values below: " << std::endl
             << "   average max" << std::endl;
    exit(-1);

  }
}



int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
    
        usage( param );
        string cu = param[ "cu" ];
        bool debug = false;
        if (param.exists( "debug" )){
            debug = true;
            // cout<<"YES!!!!"<<endl;
        }

        std::string query_file_string = param[ "query" ];
        char* query_file = new char[query_file_string.length()+1];
        memcpy(query_file, query_file_string.c_str(), query_file_string.length()+1);


        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, int> stopwords = read_stopwords();
        map<string, float> idf;
        map<string, vector<string> > queries;

        r.openRead( rep_name );
        vector<string> query_words = get_query_words(r,query_file,queries);
        get_statistics(r,idf,query_words);
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}

        map<string, vector <vector<string> > > query_2words_vector = get_2words_vector(queries);
        int n = get_collection_size(r);
        map<string, map<string, float> > term_relatedness = get_term_relatedness(r,query_2words_vector,n,queries,idf);

        // cout<<"finished geting results"<<endl;
        // cout<<"finished geting result map"<<endl;
        show_relatedness(term_relatedness,cu);


        // for(map<string,float>:: iterator it=average_idf.begin(); it!=average_idf.end(); ++it){

        //     cout<<it->first<<" "<<it->second<<endl;
        // }
        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}