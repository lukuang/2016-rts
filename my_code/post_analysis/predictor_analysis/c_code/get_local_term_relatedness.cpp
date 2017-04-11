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



map<string, vector<string> > get_results(char* result_file, const int& tune_documents){
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



float get_log_idf(const vector< map<string,int> >& one_result_term_map,const string& term){
    int count = 0;
    for(vector< map<string,int> >::const_iterator it=one_result_term_map.begin();it!=one_result_term_map.end();++it){
        map<string,int> doc_term_map = *it;
        if(doc_term_map.find(term)!=doc_term_map.end() ){
            count += 1;
        }
        
    }
    int size = one_result_term_map.size();
    if(count == 0||size == 0){
        return .0;
    }
    else{
        float idf=(size*1.0)/count;
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



float get_local_pmi(const vector< map<string,int> >& one_result_term_map,const string& term1, const string& term2){
    int common_count = 0;
    int t1_count = 0;
    int t2_count = 0;
    for(vector< map<string,int> >::const_iterator it=one_result_term_map.begin();it!=one_result_term_map.end();++it){
        map<string,int> doc_term_map = *it;
        if(doc_term_map.find(term1)!=doc_term_map.end() ){
            t1_count += 1;
        }
        if(doc_term_map.find(term2)!=doc_term_map.end()){
            t2_count += 1;
        }
        if(doc_term_map.find(term1)!=doc_term_map.end() &&
           doc_term_map.find(term2)!=doc_term_map.end()){
            
            common_count += 1;
        }
    }
    int size = one_result_term_map.size();
    if(t1_count==0 || t2_count==0 || common_count == 0 || size==0 ){
        return .0;
    }
    else{
        float probability = (size*common_count*1.0)/(t1_count*t2_count);
        return log(probability); 
    }

    
}

map<string, map<string, float> >  get_term_local_relatedness(map<string, vector< map<string,int> > >& result_term_map, map<string, vector <vector<string> > > query_2words_vector,map<string, vector<string> >& queries){
    map<string, map<string, float> >  local_term_relatedness;
    for(map<string, vector <vector<string> > >::const_iterator it=query_2words_vector.begin();it!=query_2words_vector.end();++it){
        string qid = it->first;
        map <string,float> one_query_relatedness ;
        if(it->second.size()!=0){
            vector <vector<string> > one_query_2words_vector = it->second;
            for(vector <vector<string> >::const_iterator oit=one_query_2words_vector.begin(); oit!=one_query_2words_vector.end(); ++oit){

                string subquery_string = (*oit)[0] + " " + (*oit)[1];
                one_query_relatedness[subquery_string] = get_local_pmi(result_term_map[qid],(*oit)[0],(*oit)[1]);

            }
            
        }
        else{
            one_query_relatedness[queries[qid][0]] = get_log_idf(result_term_map[qid],queries[qid][0]);
        }
        local_term_relatedness[it->first] = one_query_relatedness;
    }
    return local_term_relatedness;
}





void show_local_relatedness( map<string, map<string, float> > local_term_relatedness,const string& cu){
    for(map<string, map<string, float> >::iterator it=local_term_relatedness.begin(); it!=local_term_relatedness.end();++it){
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
        cout << it->first<<" "<<final_value<<endl;
    }

}











static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query") ) || 
      !( param.exists( "index") ) ||
      !( param.exists( "result")) ||
      !( param.exists( "cu")    ) )  {
   std::cerr << "get_term_local_relatedness usage: " << std::endl
             << "   get_term_local_relatedness -query=myquery -index=myindex -result=myresult" << std::endl;
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

        std::string result_file_string = param[ "result" ];
        char* result_file = new char[result_file_string.length()+1];
        memcpy(result_file, result_file_string.c_str(), result_file_string.length()+1);

        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, int> stopwords = read_stopwords();
        map<string, vector<string> > queries;

        r.openRead( rep_name );
        vector<string> query_words = get_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}
        int tune_documents = param.get("tune_documents",10);
        
        map<string, vector <vector<string> > > query_2words_vector = get_2words_vector(queries);
        map<string, vector<string> > results = get_results(result_file,tune_documents);
        // cout<<"finished geting results"<<endl;
        map<string, vector< map<string,int> > > result_term_map = get_result_term_map(r,results);

        map<string, map<string, float> > local_term_relatedness = get_term_local_relatedness(result_term_map,query_2words_vector,queries);

        // cout<<"finished geting results"<<endl;
        // cout<<"finished geting result map"<<endl;
        show_local_relatedness(local_term_relatedness,cu);


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