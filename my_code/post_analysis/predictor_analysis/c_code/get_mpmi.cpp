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

                // vector< vector<int> > sub_index_vector_full_size = get_index_vector(i+2,end,size);
                // for(vector< vector<int> >::iterator iit=sub_index_vector_full_size.begin(); iit!=sub_index_vector_full_size.end();++iit){
                //     index_vector.push_back(*iit);
                // }
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

map<string, vector <vector<string> > > get_subwords_vector( map<string, vector<string> >& queries, const bool& debug ){
    map<string, vector <vector<string> > > query_subwords_vector ;
    for(map<string, vector<string> >::iterator it=queries.begin(); it!=queries.end();++it){
        vector< vector<string> > subwords_vector;
        if (debug){
            cout<<"For Query "<<it->first<<":"<<endl;
            cout<<"\t";
            for(int k=0;k<it->second.size();k++){
                cout<<" "<<it->second[k];
            }
            cout<<endl;
        }
        if(it->second.size()>=1){
            for(int i =2; i<=min(int(it->second.size()),5);i++){
                int end_index = it->second.size()-1;
                int sub_vector_size = i;
                vector< vector<int> > sub_index_vector = get_index_vector(0,end_index,sub_vector_size); 
                for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                    vector<string> temp_word_vector;
                    for(std::vector<int>::iterator sit=(*iit).begin(); sit!=(*iit).end();++sit){
                        temp_word_vector.push_back(it->second[*sit]);
                    }
                    subwords_vector.push_back(temp_word_vector);
                    if (debug){
                        cout<<"\tadd:";
                        for(int k=0;k<temp_word_vector.size();k++){
                            cout<<" "<<temp_word_vector[k];
                        }
                        cout<<endl;
                    }
                }
            }
        }
        query_subwords_vector[it->first] = subwords_vector;
    }
    return query_subwords_vector;
}

float get_weight(const string& weight_scheme,int subquery_size,int query_size){
    if(weight_scheme=="linear"){
        return float(subquery_size);
    }
    else if(weight_scheme=="log"){
        return log2(subquery_size);
    }
    else if(weight_scheme=="linear_normalized"){
        return subquery_size*1.0/query_size;
    }
    else if(weight_scheme=="log_normalized"){
        if (query_size==1){
            return 1.0;
        }
        float log_sum = .0;
        for(int i=2; i<=query_size; i++){
            log_sum += log2(i);
        }
        return log2(subquery_size)/log_sum;
    }
    else{
        cout<<"the weight_scheme: "<<weight_scheme<<" is not supported!"<<endl;
        exit(-1);
    }

}

void show_unweighted_coherence( map<string, vector <vector<string> > >& query_subwords_vector, map<string, vector <int> >& co_occurrence_map,const string& cu,const bool& debug, const int& tn, map<string, vector<string> >& queries, const string& weight_scheme,map<string, map<string,int> >& local_df, map<string,int>& result_size ){
    for(map<string, vector <vector<string> > >::iterator it=query_subwords_vector.begin(); it!=query_subwords_vector.end();++it){
        string qid = it->first;
        if(debug) cout << it->first<<":"<<endl;
        map<int,float> output_mpmi ;
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
            int now_count = co_occurrence_map[it->first][i];
            if(debug) cout<<"; co-occurrence count:"<< now_count<<endl;
            float mpmi = now_count/result_size[qid];
            if(debug) cout<<"\t\tdf:"<<endl;
            for(vector<string>::iterator wit=it->second[i].begin();wit!=it->second[i].end();++wit){
                if(debug) cout<<"\t\t"<<*wit<<":"<<local_df[qid][*wit]<<endl;
                if(local_df[qid][*wit]==0){
                    mpmi = 0;
                    break;
                }
                else{
                    mpmi /= local_df[qid][*wit]*1.0/result_size[qid];
                }
            }
            if(debug) cout<<"\tnow mpmi:"<<mpmi<<endl;
            if(mpmi<=1){
                mpmi = .0;
            }
            else{
                mpmi = log2(mpmi);
            }
            if(debug) cout<<"; final mpmi value:"<< mpmi<<endl;


            if(cu=="max"){
                if(output_mpmi.find(subquery_size)!=output_mpmi.end()){

                    if(mpmi>output_mpmi[subquery_size]){
                        output_mpmi[subquery_size] = mpmi;
                    }

                }
                else{
                   output_mpmi[subquery_size] = mpmi;
                }
            }
            else if(cu=="average"){
                if(output_mpmi.find(subquery_size)==output_mpmi.end()){
                    output_mpmi[subquery_size] = 0;
                }
                output_mpmi[subquery_size] += mpmi;
                if (size_count.find(subquery_size)==size_count.end()){
                    size_count[subquery_size] = 0;
                }
                size_count[subquery_size] += 1;

            }
            
        }
        if(debug) cout<<"\toutput: ";
        float final_value = .0;
        float ideal_value = .0;
        for(map<int,float>::iterator cit=output_mpmi.begin();cit!=output_mpmi.end();++cit){
            float subquery_value ;
            float subquery_weight = get_weight(weight_scheme,cit->first,queries[qid].size()); 
            if(debug) cout<<"weight is:"<<subquery_weight<<endl;
            if(cu=="average"){
                subquery_value = cit->second*1.0/size_count[cit->first];
            }
            else{
                subquery_value = cit->second;
            }
            if(debug) cout<<cit->first<<":"<<subquery_value;
            if(debug) cout<<" final value added "<<subquery_weight*subquery_value<<", ";
            final_value += subquery_weight*subquery_value;
            ideal_value += subquery_weight*1.0;
            
            
        }
        

        if(debug) cout<<endl;
        if(output_mpmi.size()!=0){
            final_value /= ideal_value;
        }
        else{
            if(queries[qid].size()==1){
                final_value = 1.0;
            }
        }
            
        
        if(debug) cout<<"\tfinal value: "<<final_value<<endl;
        if(debug) cout<<"\tideal value: "<<ideal_value<<endl;
        cout << it->first<<" "<<final_value<<endl;
    }

}



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

map <string,int> get_result_size(map<string, vector<string> >& results){
    map<string,int> result_size ;
    for(map<string, vector<string> >::iterator it= results.begin();it!=results.end();++it){
        result_size[it->first] = it->second.size();

    }
    return result_size;
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
        // cout<<"For qid "<<it->first<<":"<<endl;
        for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){
            // cout<<"\tProcess "<<*sid<<endl;
            map<string , int> doc_term_map = get_term_map(r,*sid);
            one_result_term_map.push_back(doc_term_map);
        }

        result_term_map[it->first] = one_result_term_map;
    }
    return result_term_map;
}


int count_df_in_result(vector< map<string,int> > query_result_term_map_list,string& term){
    int df = 0;
    for(int i=0;i<query_result_term_map_list.size();i++){
        if(query_result_term_map_list[i].find(term)!=query_result_term_map_list[i].end()){
            if(query_result_term_map_list[i][term]!=0){
                df += 1;
            }
        }
    }
    return df;
}

// get df within the results for every query term
map<string, map<string,int> > get_term_local_df(map<string, vector< map<string,int> > >& result_term_map, map<string, vector<string> >& queries){
    map<string, map<string,int> > local_df;
    for(map<string, vector<string> >::iterator it=queries.begin(); it!=queries.end();++it){
        string qid = it->first;
        map<string,int> query_local_df ;
        for(int i=0;i<it->second.size();i++){
            string term = it->second[i];
            int df = count_df_in_result(result_term_map[qid],term);
            query_local_df[term] = df;
        }
        local_df[qid] = query_local_df;
    }
    return local_df;
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
  if( !param.exists( "query" ) || 
      !( param.exists( "index" ) ) ||
      !( param.exists( "result") ) ||
      !( param.exists( "weight_scheme") ) ||
      !( param.exists( "cu") )) {
   std::cerr << "get_mpmi usage: " << std::endl
             << "   get_mpmi -query=myquery -weight_scheme=weight_scheme -index=myindex -result=myresult -cu=cu_choice" << std::endl;
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
  string weight_scheme = param[ "weight_scheme" ];
  if(   weight_scheme!="log" &&
        weight_scheme!="linear" &&
        weight_scheme!="log_normalized" &&
        weight_scheme!="linear_normalized" ){
    std::cerr << "weight_scheme must be one of the values below: " << std::endl
             << "   log linear log_normalized linear_normalized" << std::endl;
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
        string weight_scheme = param[ "weight_scheme" ];
        bool debug = false;
        if (param.exists( "debug" )){
            debug = true;
            // cout<<"YES!!!!"<<endl;
        }
        int tune_documents = (int) param.get( "tune_documents", 10 );
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
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}
        if (debug) cout<<"Finished geting query words"<<endl;
        map<string, vector <vector<string> > > query_subwords_vector = get_subwords_vector(queries,debug);
        if (debug) cout<<"Finished geting query word vectors"<<endl;
        map<string, vector<string> > results = get_results(result_file,tune_documents);
        if (debug) cout<<"Finished geting results"<<endl;
        map <string,int> result_size = get_result_size(results);
        if (debug) cout<<"Finished geting result size"<<endl;

        // cout<<"finished geting results"<<endl;
        map<string, vector< map<string,int> > > result_term_map = get_result_term_map(r,results);
        if (debug) cout<<"Finished geting result map"<<endl;
        map<string, vector <int> > co_occurrence_map = get_co_occurrence_map(query_subwords_vector,result_term_map);
        if (debug) cout<<"Finished geting co-occurrence map"<<endl;
        map<string, map<string,int> > local_df = get_term_local_df(result_term_map,queries);
        if (debug) cout<<"Finished geting local df"<<endl;

        show_unweighted_coherence(query_subwords_vector,co_occurrence_map,cu,debug,tn,queries,weight_scheme,local_df,result_size);


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