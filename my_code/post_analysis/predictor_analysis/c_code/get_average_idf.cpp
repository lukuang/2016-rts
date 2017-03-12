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
using namespace std;

vector<string> get_query_words(char* query_file,  map<string, vector<string> >& queries){
    ifstream f;
    string line;
    string qid="";
    vector<string> words;
    f.open(query_file);
    if(f.is_open()){
        while(getline(f,line)){
            if ((line.find(":"))!=string::npos){
                size_t found = line.find(":");
                qid  = line.substr(0,found);
                string query_lang_string = line.substr(found+1);
                size_t query_string_begin = query_lang_string.find_first_of("(");
                size_t query_string_end = query_lang_string.find_last_of(")");
                string query_string = query_lang_string.substr(query_string_begin+1,query_string_end-query_string_begin-8);
                // cout<<qid<<":"<<query_string<<endl;

                istringstream iss(query_string);
                vector<string> tokens;
                vector<string> query_words;

                copy(istream_iterator<string>(iss),
                     istream_iterator<string>(),
                     back_inserter(tokens));
                for(vector<string>::iterator it = tokens.begin(); it!=tokens.end(); ++it){
                    if((*it).find("0123456789")==string::npos && (*it).find_first_of(".")==string::npos){
                        query_words.push_back(*it);
                        words.push_back(*it);
                        // cout<<"push back "<<*it<<endl;
                    }  

                queries[qid] = query_words;
                }

            }
            //else if((line.find("text>"))!=string::npos){
            //    is_text = !is_text;
            //}
            //else if (is_text){
            //    queries[qid]=line;
            //}
        }
    }
    else{
        cout<<"error: cannot open query file "<<query_file<<endl;
    }


    
    return words;
}

void get_statistics(indri::collection::Repository& r,map<string, float>& idf,vector<string>& query_words){

    indri::server::LocalQueryServer local(r);
    float n = 1.0*local.documentCount();
    for(vector<string>::iterator it = query_words.begin(); it!=query_words.end(); ++it){
        int df = local.documentCount(*it) ;
        if( df == 0){
            idf[*it] = .0;
        }
        else{
            idf[*it] = log(n/df );        
        }
    }
}

void output(map<string, int>& cf, map<string, int>& df,int& n,string& dest_dir){
    
    string end_str = "/";
    const char* real_end;
    real_end = &dest_dir[dest_dir.length() - 1];
    if (end_str.compare(real_end)!=0){
        dest_dir += end_str;
    }

    const char* n_file_name = (dest_dir+"n").c_str();
    ofstream n_file;
    n_file.open(n_file_name);
    n_file << n <<endl;
    n_file.close();

    const char* cf_file_name = (dest_dir+"cf").c_str();
    ofstream cf_file;
    cf_file.open(cf_file_name);
    for(map<string,int>::iterator it=cf.begin();it!=cf.end();++it){
        cf_file<< it->first <<" "<<it->second<<endl;
    }
    cf_file.close();

    const char* df_file_name = (dest_dir+"df").c_str();
    ofstream df_file;
    df_file.open(df_file_name);
    for(map<string,int>::iterator it=df.begin();it!=df.end();++it){
        df_file<< it->first <<" "<<it->second<<endl;
    }
    df_file.close();


}

map<string, float>  compute_average_idf(map<string, vector<string> >& queries,map<string, float>& idf){
    map<string, float> average_idf;
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        float query_average_idf = .0;
        string qid = it->first;
        vector<string> query_words = it->second;
         // if (qid == "MB438"){
         //    cout<<"MB438:"<<endl;
         // }
        for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
            // if (qid == "MB438"){
            //     cout<<"\t"<<*wit<<":"<<idf[*wit]<<endl;
            // }
            query_average_idf += idf[*wit];      

        }
        query_average_idf /= query_words.size();
        average_idf[qid] = query_average_idf;
    }
    return average_idf;

}

static void usage( indri::api::Parameters param ) {
  if( !param.exists( "query" ) || 
      !( param.exists( "index" ) )) {
   std::cerr << "get_average_idf usage: " << std::endl
             << "   get_average_idf -query=myquery -index=myindex" << std::endl;
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

        map<string, float> idf;
        map<string, float> average_idf;
        map<string, vector<string> > queries;

        vector<string> query_words = get_query_words(query_file,queries);
        r.openRead( rep_name );
        get_statistics(r,idf,query_words);
        // output(idf,dest_dir);

        average_idf = compute_average_idf(queries,idf);

        for(map<string,float>:: iterator it=average_idf.begin(); it!=average_idf.end(); ++it){

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