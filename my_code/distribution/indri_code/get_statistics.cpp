/* get statistics for query words given index(wt2g)
*   statistics: 
*       cf: collection frequency
*       df: document frequency
*       n: number of documents
*/


#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/QueryEnvironment.hpp"
#include <dirent.h>
#include <iostream>
#include <typeinfo>
#include <algorithm>
#include <map>
#include <fstream>
#include <dirent.h>
using namespace std;

vector<string> get_query_words(char* original_query_file){
    ifstream original_query;
    string line;
    vector<string> words;
    original_query.open(original_query_file);
    if(original_query.is_open()){
        while(getline(original_query, line)){
            words.push_back(line);
        }
    }
    return words;
}

void get_statistics(indri::collection::Repository& r,map<string, int>& cf,
    map<string, int> df,int& n,vector<string>& query_words){

    indri::server::LocalQueryServer local(r);
    n = local.documentCount();
    for(vector<string>::iterator it = query_words.begin(); it!=query_words.end(); ++it){
        
        cf[*it] = local.termCount( *it );
        df[*it] = local.documentCount(*it);
        cout<< "term "<<*it<<" with df "<<local.documentCount(*it) <<endl;
    }
}

void output(map<string, int>& cf, map<string, int> df,int& n,string& dest_dir){
    
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


int main(int argc, char** argv){
    indri::collection::Repository r;
    string rep_name = argv[1];
    //int percent_threshold = atoi(argv[2]);
    //string idf_term  = argv[3];
    //float variance_threshold = atof(argv[4]);

    char* original_query_file = argv[2];
    string dest_dir = argv[3];
    map<string, int> cf;
    map<string, int> df;
    int n;
    vector<string> query_words = get_query_words(original_query_file);
    r.openRead( rep_name );
    get_statistics(r,cf,df,n,query_words);
    output(cf,df,n,dest_dir);

    r.close();
}