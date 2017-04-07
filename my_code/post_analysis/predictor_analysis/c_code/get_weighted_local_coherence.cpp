/* get unweight local coherence of queries
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

map<string, vector <vector<string> > > get_subwords_vector( map<string, vector<string> >& queries ){
    map<string, vector <vector<string> > > query_subwords_vector ;
    for(map<string, vector<string> >::iterator it=queries.begin(); it!=queries.end();++it){
        vector< vector<string> > subwords_vector;
        if(it->second.size()>=1){
            for(int i =2; i<=it->second.size();i++){
                int end_index = it->second.size()-1;
                int sub_vector_size = i;
                vector< vector<int> > sub_index_vector = get_index_vector(0,end_index,sub_vector_size); 
                for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                    vector<string> temp_word_vector;
                    for(std::vector<int>::iterator sit=(*iit).begin(); sit!=(*iit).end();++sit){
                        temp_word_vector.push_back(it->second[*sit]);
                    }
                    subwords_vector.push_back(temp_word_vector);
                }
            }
        }
        query_subwords_vector[it->first] = subwords_vector;
    }
    return query_subwords_vector;
}

float compute_avg_idf_weight(map<string,float>& idf, const vector<string>& subquery ){
    float weight=.0;
    float subquery_size = subquery.size()*1.0;
    for(std::vector<string>::const_iterator it=subquery.begin(); it!=subquery.end();++it){
        weight += idf[*it]/subquery_size;
        // cout<< "add " <<idf[*it]/subquery_size<<" for"<<*it<<endl;
    }
    return weight;

}

// weighted coherence with idf weight
void show_weighted_coherence( map<string, vector <vector<string> > >& query_subwords_vector, map<string, vector <int> >& co_occurrence_map,const string& cu,const bool& debug, map<string, float>& idf, map<string, vector<string> >& queries, const int& tn){
    for(map<string, vector <vector<string> > >::iterator it=query_subwords_vector.begin(); it!=query_subwords_vector.end();++it){
        string qid = it->first;
        if(debug) cout << it->first<<":"<<endl;
        map<int,float> output_count ;
        map<int, int> size_count;
        for(int i=0;i<it->second.size();i++){
            if(debug){
                cout <<"\t";
                for(vector<string>::iterator wit=it->second[i].begin();wit!=it->second[i].end();++wit){
                    cout <<*wit<<" ";
                }
            }
            
            int subquery_size = it->second[i].size();

            if(tn!=0 && subquery_size!=tn){
                if(debug) cout<<";"<<endl;
                continue;
            }
            vector <string> subquery = it->second[i];
            float weight = compute_avg_idf_weight(idf,subquery);
            float now_count = co_occurrence_map[it->first][i] * weight;
            if(debug) cout<<"; co-occurrence count:"<< co_occurrence_map[it->first][i];
            if(debug) cout<<"; weight:"<< weight<<endl;
            if(cu == "binary"){
                if(output_count.find(subquery_size)==output_count.end() ){
                    
                    if(now_count>0){
                        output_count[subquery_size] = 1;
                    }
                    else{
                        output_count[subquery_size] = 0;
                    }
                }
            }
            else if(cu=="max"){
                if(output_count.find(subquery_size)!=output_count.end()){
                    if(now_count>output_count[subquery_size]){
                        output_count[subquery_size] = now_count;
                    }

                }
                else{
                   output_count[subquery_size] = now_count;
                }
            }
            else if(cu=="average"){
                if(output_count.find(subquery_size)==output_count.end()){
                    output_count[subquery_size] = 0;
                }
                output_count[subquery_size] += now_count;
                if (size_count.find(subquery_size)==size_count.end()){
                    size_count[subquery_size] = 0;
                }
                size_count[subquery_size] += 1;

            }
            
        }
        if(debug) cout<<"\toutput: ";
        float final_value = .0;
        for(map<int,float>::iterator cit=output_count.begin();cit!=output_count.end();++cit){
            float subquery_value ;
            if(cu=="average"){
                subquery_value = cit->second*1.0/size_count[cit->first];
            }
            else{
                subquery_value = cit->second;
            }
            if(debug) cout<<cit->first<<":"<<subquery_value;
            if(debug) cout<<" final value added "<<log2(cit->first)*subquery_value<<", ";
            final_value += subquery_value;
            
            
        }
        if(cu!="binary"){
                final_value /= 10.0;
        }

        if(debug) cout<<endl;
        if(output_count.size()==0){
            if (queries[qid].size()==1){
                final_value = idf[queries[qid][0]];
                if (debug) cout<<"\tsingle term query "<<qid<<" get weight "<<final_value<<endl;
            }
            else{
                if (debug) cout<<"\non-single term query "<<qid<<" get weight "<<final_value<<endl;

            }
        }
            
        
        if(debug) cout<<"\tfinal value: "<<final_value<<endl;
        cout << it->first<<" "<<final_value<<endl;
    }

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

float compute_pmi_weight(indri::collection::Repository& r,const string& term1, const string& term2, const int& n){
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



// weighted coherence with pmi weight
void show_weighted_coherence( map<string, vector <vector<string> > >& query_subwords_vector, map<string, vector <int> >& co_occurrence_map,const string& cu,const bool& debug, const int& tn, indri::collection::Repository& r,  map<string, vector<string> >& queries){
    int n = get_collection_size(r);
    for(map<string, vector <vector<string> > >::iterator it=query_subwords_vector.begin(); it!=query_subwords_vector.end();++it){
        string qid = it->first;
        if(debug) cout << it->first<<":"<<endl;
        map<int,float> output_count ;
        map<int, int> size_count;
        for(int i=0;i<it->second.size();i++){
            if(debug){
                cout <<"\t";
                for(vector<string>::iterator wit=it->second[i].begin();wit!=it->second[i].end();++wit){
                    cout <<*wit<<" ";
                }
            }
            
            int subquery_size = it->second[i].size();
            if(tn!=0 && subquery_size!=tn){
                continue;
            }
            vector<string> subquery = it->second[i];
            float weight = compute_pmi_weight(r,subquery[0],subquery[1],n);
            float now_count = co_occurrence_map[it->first][i]*weight;
            if(debug) cout<<"; co-occurrence count:"<< co_occurrence_map[it->first][i];
            if(debug) cout<<"; weight:"<< weight<<endl;
            if(cu == "binary"){
                if(output_count.find(subquery_size)==output_count.end() ){
                    
                    if(now_count>0){
                        output_count[subquery_size] = 1;
                    }
                    else{
                        output_count[subquery_size] = 0;
                    }
                }
            }
            else if(cu=="max"){
                if(output_count.find(subquery_size)!=output_count.end()){
                    if(now_count>output_count[subquery_size]){
                        output_count[subquery_size] = now_count;
                    }

                }
                else{
                   output_count[subquery_size] = now_count;
                }
            }
            else if(cu=="average"){
                if(output_count.find(subquery_size)==output_count.end()){
                    output_count[subquery_size] = 0;
                }
                output_count[subquery_size] += now_count;
                if (size_count.find(subquery_size)==size_count.end()){
                    size_count[subquery_size] = 0;
                }
                size_count[subquery_size] += 1;

            }
            
        }
        if(debug) cout<<"\toutput: ";
        float final_value = .0;
        for(map<int,float>::iterator cit=output_count.begin();cit!=output_count.end();++cit){
            float subquery_value ;
            if(cu=="average"){
                subquery_value = cit->second*1.0/size_count[cit->first];
            }
            else{
                subquery_value = cit->second;
            }
            if(debug) cout<<cit->first<<":"<<subquery_value;
            if(debug) cout<<" final value added "<<log2(cit->first)*subquery_value<<", ";
            final_value += log2(cit->first)*subquery_value;
            
            
        }
        if(cu!="binary"){
                final_value /= 10.0;
        }

        if(debug) cout<<endl;
        if(output_count.size() ==0){
            if(queries[qid].size()==0){
                final_value = get_log_idf(r,n,queries[qid][0]);
            }
        }
        
            
        
        if(debug) cout<<"\tfinal value: "<<final_value<<endl;
        cout << it->first<<" "<<final_value<<endl;
    }

}



map<string, vector<string> > get_results(char* result_file,const int& tune_documents){
    ifstream f;
    string line;
    string qid="";
    map<string, vector<string> > results;
    f.open(result_file);
    if(f.is_open()){
        while(getline(f,line)){
            size_t qid_founder = line.find_first_of(" ");
            if (qid_founder!=string::npos){
                qid = line.substr(0,qid_founder);
                if(results.find( qid ) == results.end()){
                    results[qid] = vector<string>();
                }
                line = line.substr(qid_founder+4);
                size_t docid_finder = line.find_first_of(" ");
                if(docid_finder != string::npos){
                    if(results[qid].size()==tune_documents){
                        continue;
                    }
                    else{
                        string docid = line.substr(0,docid_finder);
                        results[qid].push_back(docid);
                    }
                    
                }

            }
        }
    }
    return results;
}

lemur::api::DOCID_T get_internal_did( indri::collection::Repository& r, const string& ex_docid ) {
  indri::collection::CompressedCollection* collection = r.collection();
  std::string attributeName = "docno";
  std::vector<lemur::api::DOCID_T> documentIDs;

  documentIDs = collection->retrieveIDByMetadatum( attributeName, ex_docid );

  return documentIDs[0];

}

map<string , int> get_term_map(indri::collection::Repository& r,const string& ex_docid){
    lemur::api::DOCID_T internal_did = get_internal_did(r,ex_docid);
    map <string, int> term_map;
    indri::server::LocalQueryServer local(r);

    std::vector<lemur::api::DOCID_T> documentIDs;
    documentIDs.push_back(internal_did);
    indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );

    if( response->getResults().size() ) {
        indri::api::DocumentVector* docVector = response->getResults()[0];

        for( size_t i=0; i<docVector->positions().size(); i++ ) {
          int position = docVector->positions()[i];
          const std::string& stem = docVector->stems()[position];

          if(term_map.find(stem)==term_map.end()){
            term_map[stem] = 0;
          }
          term_map[stem] += 1;
        }
        delete docVector;
    }

    delete response;
    return term_map;
}

map<string, vector< map<string,int> > > get_result_term_map(indri::collection::Repository& r, const map<string, vector<string> >& results){
    map<string, vector< map<string,int> > > result_term_map;
    for(map<string, vector<string> >::const_iterator it=results.begin();it!=results.end(); ++it ){
        vector< map<string,int> > one_result_term_map;
        for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){
            map<string , int> doc_term_map = get_term_map(r,*sid);
            one_result_term_map.push_back(doc_term_map);
        }

        result_term_map[it->first] = one_result_term_map;
    }
    return result_term_map;
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





static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" ) ) || 
      !( param.exists( "index" ) ) ||
      !( param.exists( "result") ) ||
      !( param.exists( "weight") ) ||
      !( param.exists( "cu"    ) ) ) {
   std::cerr << "get_weighted_local_coherence usage: " << std::endl
             << "   get_weighted_local_coherence -query=myquery -index=myindex -result=myresult -cu=cu_choice -weight=weight_choice" << std::endl;
   exit(-1);
  }
  string cu = param[ "cu" ];
  if(  cu!="binary" &&
            cu!="average" &&
            cu!="max" ){
    std::cerr << "cu must be one of the values below: " << std::endl
             << "   binary average max" << std::endl;
    exit(-1);

  }
  string weight = param[ "weight" ];
  if(   weight!="idf" &&
        weight!="pmi"  ){
    std::cerr << "weight must be one of the values below: " << std::endl
             << "   idf pmi" << std::endl;
    exit(-1);

  }
  int tn ;
  if (param.exists( "tn" )){
        string tn_string  = param[ "tn" ];
        tn = atoi(tn_string.c_str());
        // cout<<"YES!!!!"<<endl;
        if( tn!=2 &&   weight=="pmi" ){
            cout << "If using pmi weight, the term size should be 2!"<<endl;
            exit(-1);
        }

  }
  else{
    if( weight=="pmi" ){
        cout << "If using pmi weight, must specify term size (should be 2)!"<<endl;
            exit(-1);
    }
  }

}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
    
        usage( param );
        string cu = param[ "cu" ];
        string weight = param[ "weight" ];
        bool debug = false;
        if (param.exists( "debug" )){
            debug = true;
            // cout<<"YES!!!!"<<endl;
        }
        int tn = 0;
        if (param.exists( "tn" )){
            string tn_string  = param[ "tn" ];
            tn = atoi(tn_string.c_str());
            // cout<<"YES!!!!"<<endl;
        }
        std::string query_file_string = param[ "query" ];
        char* query_file = new char[query_file_string.length()+1];
        memcpy(query_file, query_file_string.c_str(), query_file_string.length()+1);

        std::string result_file_string = param[ "result" ];
        char* result_file = new char[result_file_string.length()+1];
        memcpy(result_file, result_file_string.c_str(), result_file_string.length()+1);

        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, vector<string> > queries;

        r.openRead( rep_name );
        vector<string> query_words = get_query_words(r,query_file,queries);
        
        int tune_documents = param.get("tune_documents",10);
        
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}

        map<string, vector <vector<string> > > query_subwords_vector = get_subwords_vector(queries);
        map<string, vector<string> > results = get_results(result_file,tune_documents);
        // cout<<"finished geting results"<<endl;
        map<string, vector< map<string,int> > > result_term_map = get_result_term_map(r,results);
        // cout<<"finished geting result map"<<endl;
        map<string, vector <int> > co_occurrence_map = get_co_occurrence_map(query_subwords_vector,result_term_map);
        if(weight == "idf"){
            map<string, float> idf;
            get_statistics(r,idf,query_words);
            
            show_weighted_coherence(query_subwords_vector,co_occurrence_map,cu,debug,idf,queries,tn );
        }
        else{
            if(debug) cout<<"Using pmi weight!"<<endl;
            show_weighted_coherence(query_subwords_vector,co_occurrence_map,cu,debug,tn,r, queries);

        }



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