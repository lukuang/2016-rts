/* create the minimun spanning tree of the term relatedness
and return the results
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
#include <limits.h>
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


map<string, vector <vector<int> > > get_2words_index_vector( map<string, vector<string> >& queries ){
    map<string, vector <vector<int> > > query_2words_index_vector ;
    for(map<string, vector<string> >::iterator it=queries.begin(); it!=queries.end();++it){
        vector< vector<int> > subwords_index_vector;
        // cout<<"for query "<<it->first<<" add :"<<endl;
        if(it->second.size()>=1){
            
            int end_index = it->second.size()-1;
            int sub_vector_size = 2;
            vector< vector<int> > sub_index_vector = get_index_vector(0,end_index,sub_vector_size); 
            for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                vector<int> temp_word_vector;
                temp_word_vector.push_back( (*iit)[0] );
                temp_word_vector.push_back( (*iit)[1] );
                subwords_index_vector.push_back(temp_word_vector);
                // cout<<"\t";
                // for(int k=0;k<temp_word_vector.size();k++ ){
                //     cout<<" "<<temp_word_vector[k];
                // }
                // cout<<endl;
            }
        
        }
        query_2words_index_vector[it->first] = subwords_index_vector;
    }
    return query_2words_index_vector;
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



vector <vector<float> > get_pmi_negative_weight_matrix(indri::collection::Repository& r,const int& n, vector<string>& query_words, vector <vector<int> >& one_query_2words_index_vector,const bool& debug){
    int word_size = query_words.size();
    vector <vector<float> > pmi_matrix(word_size,vector<float>(word_size,.0) ) ;
    for(int i=0;i<one_query_2words_index_vector.size();i++){
        int  j = one_query_2words_index_vector[i][0];
        int  k = one_query_2words_index_vector[i][1];
        float single_pmi = -1*get_pmi(r,query_words[j],query_words[k],n);
        if (debug) cout<<"\tweight between "<<query_words[j]<<" "<<query_words[k]<<" is "<<single_pmi<<endl;
        pmi_matrix[j][k] = single_pmi;
        pmi_matrix[k][j] = single_pmi;
    }
    if(debug){
        cout<<"\tShow matrix:\n"<<endl;
        cout<<"\t\t";
        for(int i=0;i<word_size;i++){
            cout<<query_words[i]<<" ";

        }
        cout<<endl;
        for(int i=0;i<word_size;i++){
            cout<<"\t\t";
            for(int j=0;j<word_size;j++){
                cout<<pmi_matrix[i][j]<<" ";
            }
            cout<<endl;
        }
    }
    return pmi_matrix;
}


int minKey(vector<float>& key, vector<bool> mstSet)
{
   // Initialize min value
   int V = key.size();
   float min = FLT_MAX, min_index;
 
   for (int v = 0; v < V; v++)
     if (mstSet[v] == false && key[v] < min)
         min = key[v], min_index = v;
 
   return min_index;
}

// Function to construct and print MST for a graph represented using adjacency
// matrix representation
float get_mst_value(const vector< vector<float> >& pmi_matrix,vector<string>& query_words,const bool& debug)
{
    if(debug) cout<<"\tGet mst:"<<endl;
    float mst_value = .0;
     int V = pmi_matrix.size();
     vector<int> parent(V,0); // Array to store constructed MST
     vector<float> key(V,0);   // Key values used to pick minimum weight edge in cut
     vector<bool> mstSet(V,false);  // To represent set of vertices not yet included in MST
 
     // Initialize all keys as INFINITE
     for (int i = 0; i < V; i++)
        key[i] = FLT_MAX, mstSet[i] = false;
 
     // Always include first 1st vertex in MST.
     key[0] = .0;     // Make key 0 so that this vertex is picked as first vertex
     parent[0] = -1; // First node is always root of MST 
 
     // The MST will have V vertices
     for (int count = 0; count < V-1; count++)
     {
        // Pick the minimum key vertex from the set of vertices
        // not yet included in MST
        int u = minKey(key, mstSet);
        // Add the picked vertex to the MST Set
        mstSet[u] = true;
 
        if (debug) {
            if (count != 0){
                cout<<"\tChoose word "<<query_words[u]<<" for edge "<<query_words[parent[u]]<<" - "<<query_words[u]<<endl;
            }
        }
        // Update key value and parent index of the adjacent vertices of
        // the picked vertex. Consider only those vertices which are not yet
        // included in MST
        for (int v = 0; v < V; v++)
 
           // graph[u][v] is non zero only for adjacent vertices of m
           // mstSet[v] is false for vertices not yet included in MST
           // Update the key only if graph[u][v] is smaller than key[v]
          if ( (u!=v) && mstSet[v] == false && pmi_matrix[u][v] <  key[v]){
             if(debug){
                cout<<"\t\tUpdate the shortest word to "<<query_words[v]<<" as "<< query_words[u]<<endl;
                cout<<"\t\tprevious weight: "<<key[v]<<" to "<<pmi_matrix[u][v]<<endl;
             }
             parent[v]  = u;
             key[v] = pmi_matrix[u][v];
             
          }
     }
    if(debug){
     // print the constructed MST
        printf("\tEdge   Weight\n");
        for (int i = 1; i < V; i++){
            cout<<"\t"<<query_words[parent[i]]<<" - "<<query_words[i]<<" "<<pmi_matrix[i][parent[i]]<<endl;
        }
    }
     for (int i = 1; i < V; i++){
        mst_value += -1*pmi_matrix[i][parent[i]];
     }
     return mst_value;
}

map<string,  float >  get_mst_term_relatedness(indri::collection::Repository& r, map<string, vector <vector<int> > > query_2words_index_vector,const int& n,map<string, vector<string> >& queries, const bool& debug){
    map<string, float >  mst_term_relatedness;
    for(map<string, vector <vector<int> > >::const_iterator it=query_2words_index_vector.begin();it!=query_2words_index_vector.end();++it){
        string qid = it->first;
        if(debug) cout<<"For query "<<qid<<":"<<endl;
        if(it->second.size()!=0){
            vector <vector<int> > one_query_2words_index_vector = it->second;
            vector <vector<float> > pmi_matrix = get_pmi_negative_weight_matrix(r, n, queries[qid],one_query_2words_index_vector,debug);
            mst_term_relatedness[qid] = get_mst_value(pmi_matrix,queries[qid],debug)/ (queries[qid].size()-1);
            
        }
        else{
            if(debug) cout<< "single query!"<<endl;
            mst_term_relatedness[qid] = get_log_idf(r,n,queries[qid][0]);

        }
    }
    return mst_term_relatedness;
}





void show_mst_relatedness( map<string, float > mst_term_relatedness){
    for(map<string, float >::iterator it=mst_term_relatedness.begin(); it!=mst_term_relatedness.end();++it){
        
        cout << it->first<<" "<<it->second<<endl;
    }

}











static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query") ) || 
      !( param.exists( "index") ) ) {
   std::cerr << "get_mst_term_relatedness usage: " << std::endl
             << "   get_mst_term_relatedness -query=myquery -index=myindex" << std::endl;
   exit(-1);
  }
  
}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
    
        usage( param );
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
        map<string, vector<string> > queries;

        r.openRead( rep_name );
        vector<string> query_words = get_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}

        map<string, vector <vector<int> > > query_2words_index_vector = get_2words_index_vector(queries);
        int n = get_collection_size(r);
        map<string,  float > mst_term_relatedness = get_mst_term_relatedness(r,query_2words_index_vector,n,queries,debug);

        // cout<<"finished geting results"<<endl;
        // cout<<"finished geting result map"<<endl;
        show_mst_relatedness(mst_term_relatedness);


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