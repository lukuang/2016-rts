/* get collection score by treating the whole collection as a document
based on the retrieval method
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




map<string, float>  compute_collection_score(indri::collection::Repository& r,map<string, vector<string> >& queries,const string& retrieval_method){
    indri::server::LocalQueryServer local(r);

    float avdl = get_avdl(r);
    map<string, float> collection_score;
    float n = 1.0*local.documentCount();
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        float query_collection_score = .0;
        string qid = it->first;
        vector<string> query_words = it->second;
         // if (qid == "MB438"){
         //    cout<<"MB438:"<<endl;
         // }
        if(retrieval_method=="f2exp"){
          for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
                // if (qid == "MB438"){
                //     cout<<"\t"<<*wit<<":"<<idf[*wit]<<endl;
                // }
                int f_ct = local.stemCount(*wit);
                int df = local.documentStemCount(*wit);

                if(f_ct!=0 && df!=0){
                    float idf = (n+1)*1.0/ df;
                    double numerator = idf * f_ct;
                    double denominator = f_ct + 0.1 + (0.1*n);
                    query_collection_score +=  numerator / denominator;                
                }

            }  
        }
        else if(retrieval_method=="dirichlet"){
            for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
                
                int f_ct = local.stemCount(*wit);
                int c_size = local.termCount();
                int mu = 500;
                float p_wc = f_ct*1.0/c_size;
                if(p_wc!=0 ){
                    double numerator =  p_wc + mu*p_wc;
                    double denominator = mu+c_size;
                    query_collection_score +=  log(numerator / denominator);                
                }

            }
        }
        else if(retrieval_method=="pivoted"){
            for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
                
                int f_ct = local.stemCount(*wit);
                int df = local.documentStemCount(*wit);
                int d_size = local.documentCount();
                float s = 0.2;
                if(f_ct!=0 && df!=0){
                    float idf = log((d_size+1)*1.0/df);
                    double numerator = idf*(1 + log( 1 + log(f_ct) ) );
                    double denominator = (1-s) + s*(d_size);
                    query_collection_score +=  numerator / denominator;                
                }

            }
        }
        else if(retrieval_method=="bm25"){
            for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
                
                float k1=1.0;
                int k3=1000;
                float b = 0.75;

                int f_ct = local.stemCount(*wit);
                int df = local.documentStemCount(*wit);
                int d_size = local.documentCount();

                if(f_ct!=0 && df!=0){
                    float idf = log( (d_size-df+0.5)*1.0/(df+0.5)  );
                    double numerator = idf * (k1+1)*f_ct ;
                    double denominator = k1*( (1-b) + b*d_size ) + f_ct;
                    query_collection_score +=  numerator / denominator;                
                }

            }
        }
        else{
            cout<<"The method "<<retrieval_method<<" is not implemented!"<<endl;
            exit(-1);
        }
        
        collection_score[qid] = query_collection_score;
    }
    return collection_score;

}

static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" )) || 
      !( param.exists( "index" )) ||
      !( param.exists( "retrieval_method" ))  ) {
   std::cerr << "get_collection_score usage: " << std::endl
             << "get_collection_score -query=myquery -index=myindex -retrieval_method=retrieval_method" << std::endl;
   exit(-1);
  }
}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
        usage( param );
        std::string query_file_string = param[ "query" ];
        char* query_file = new char[query_file_string.length()+1];
        memcpy(query_file, query_file_string.c_str(), query_file_string.length()+1);

        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, float> collection_score;
        map<string, vector<string> > queries;
        r.openRead( rep_name );
        
        vector<string> query_words = get_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        std::string retrieval_method = param[ "retrieval_method" ];
        collection_score = compute_collection_score(r,queries,retrieval_method);

        for(map<string,float>:: iterator it=collection_score.begin(); it!=collection_score.end(); ++it){

            cout<<it->first<<" "<<it->second<<endl;
        }
        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}