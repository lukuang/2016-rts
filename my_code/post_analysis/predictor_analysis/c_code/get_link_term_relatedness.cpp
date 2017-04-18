/* create relatedness representation for queries based on the
links produced by stanford parser
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


void get_query_links(indri::collection::Repository& r,char* query_link_file,map<string, vector <vector<string> > >& query_links, const bool& debug){
    map<string, int> stopwords = read_stopwords();
    ifstream f;

    string line;
    string qid="";
    vector<string> words;
    f.open(query_link_file);
    if(f.is_open()){
        while(getline(f,line)){
            if ((line.find(":"))!=string::npos){
                size_t found = line.find(":");
                qid  = line.substr(0,found);
                vector< vector<string> > single_query_links;

                string link_strings = line.substr(found+1);
                found = link_strings.find_first_of(",");
                while(found!=string::npos){
                    string sinlge_link = link_strings.substr(0,found); 
                    link_strings = link_strings.substr(found+1); 
                    size_t space = sinlge_link.find_first_of(" ");
                    if(space!=string::npos){
                        string first_word = r.processTerm( sinlge_link.substr(0,space) );
                        string second_word = r.processTerm( sinlge_link.substr(space+1) );
                        if(stopwords.find(first_word)==stopwords.end() && stopwords.find(second_word)==stopwords.end()){
                            vector<string>  temp_link;
                            temp_link.push_back(first_word);
                            temp_link.push_back(second_word);
                            single_query_links.push_back(temp_link);
                        }
                    }
                    else{
                        cout<<"ERROR: There is not space in the following link for query "<<qid<<endl;
                        cout<<sinlge_link<<endl;
                        exit(-1);
                    }

                    found = link_strings.find_first_of(",");

                }
                query_links[qid] = single_query_links;
            }
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









map<string,  float >  get_link_term_relatedness(indri::collection::Repository& r, map<string, vector <vector<string> > >& query_links,const int& n, map<string, vector<string> >& queries,const bool& debug){
    map<string, float >  link_term_relatedness;
    for(map<string, vector <vector<string> > >::iterator it=query_links.begin();it!=query_links.end();++it){
        string qid = it->first;
        if(debug) cout<<"For query "<<qid<<":"<<endl;
        if(it->second.size()!=0){
            link_term_relatedness[qid] = .0;
            for(vector <vector<string> >::iterator lit=it->second.begin(); lit!=it->second.end(); ++lit){
                float pmi = get_pmi(r,(*lit)[0],(*lit)[1],n);
                if (debug) cout<<"\tadd link "<<(*lit)[0]<<" - "<<(*lit)[1]<<" with weight "<<pmi<<endl;
                link_term_relatedness[qid] += pmi; 
            }

            link_term_relatedness[qid] /= 1.0*query_links[qid].size();
            
        }
        else{
            if(debug) cout<< "single query!"<<endl;
            link_term_relatedness[qid] = get_log_idf(r,n,queries[qid][0]);

        }
    }
    return link_term_relatedness;
}





void show_link_relatedness( map<string, float > link_term_relatedness){
    for(map<string, float >::iterator it=link_term_relatedness.begin(); it!=link_term_relatedness.end();++it){
        
        cout << it->first<<" "<<it->second<<endl;
    }

}











static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "link" ) ) || 
      !( param.exists( "index") ) ||
      !( param.exists( "query") ) ) {
   std::cerr << "get_link_term_relatedness usage: " << std::endl
             << "   get_link_term_relatedness -query=myquery -link=mylink -index=myindex" << std::endl;
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


        std::string query_link_file_string = param[ "link" ];
        char* query_link_file = new char[query_link_file_string.length()+1];
        memcpy(query_link_file, query_link_file_string.c_str(), query_link_file_string.length()+1);


        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, int> stopwords = read_stopwords();
        map<string, vector<string> > queries;
        map<string, vector <vector<string> > > query_links;

        r.openRead( rep_name );

        vector<string> query_words = get_query_words(r,query_file,queries);
        
        get_query_links(r,query_link_file,query_links,debug);
        
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}

        int n = get_collection_size(r);
        map<string,  float > link_term_relatedness = get_link_term_relatedness(r,query_links,n,queries,debug);

        // cout<<"finished geting results"<<endl;
        // cout<<"finished geting result map"<<endl;
        show_link_relatedness(link_term_relatedness);


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