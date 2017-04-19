
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

map <string,int> read_stopwords(indri::collection::Repository& r){
  char file_name[] = "/usa/lukuang/data/new_stopwords";
  ifstream stopwords;
  stopwords.open(file_name);
  string needed = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM";
  map <string,int> local;
  string line;
  if(stopwords.is_open()){
    while(getline(stopwords,line)){
      size_t found=line.find_first_of(needed);
      if(found==string::npos){
        continue;
      }
      else{
        size_t found2=line.find_last_of(needed);
        if(found2!=string::npos){
          string stem = r.processTerm( line.substr(found,(found2-found+1)) );
          local[stem]=0;
        }
      }


    }
  }
  else cout<< "cannot open stop word file"<<endl;

  /*map <string,int >::iterator iter;
  for ( iter = local.begin( ); iter != local.end( ); iter++ ){
    cout<<iter->first<<endl;
  }*/
  return (local);

}


map <string,int> read_stopwords(){
  char file_name[] = "/usa/lukuang/data/new_stopwords";
  ifstream stopwords;
  stopwords.open(file_name);
  string needed = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM";
  map <string,int> local;
  string line;
  if(stopwords.is_open()){
    while(getline(stopwords,line)){
      size_t found=line.find_first_of(needed);
      if(found==string::npos){
        continue;
      }
      else{
        size_t found2=line.find_last_of(needed);
        if(found2!=string::npos){
          local[line.substr(found,(found2-found+1))]=0;
        }
      }


    }
  }
  else cout<< "cannot open stop word file"<<endl;

  /*map <string,int >::iterator iter;
  for ( iter = local.begin( ); iter != local.end( ); iter++ ){
    cout<<iter->first<<endl;
  }*/
  return (local);

}

vector<string> get_unstemmed_query_words(indri::collection::Repository& r, char* query_file,  map<string, vector<string> >& queries){
    map<string, int> stopwords = read_stopwords();
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

                map<string,int> stem_map;
                copy(istream_iterator<string>(iss),
                     istream_iterator<string>(),
                     back_inserter(tokens));
                for(vector<string>::iterator it = tokens.begin(); it!=tokens.end(); ++it){
                    if((*it).find("0123456789")==string::npos && (*it).find_first_of(".")==string::npos){
                        if(stopwords.find(*it)==stopwords.end()){
                            string stem = r.processTerm(*it);
                            if(stem_map.find(stem)==stem_map.end()){
                                stem_map[stem] = 0;
                                query_words.push_back( *it);

                                words.push_back(*it);
                                // cout<<"push back "<<*it<<endl;
                            }
                        }
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



vector<string> get_query_words(indri::collection::Repository& r, char* query_file,  map<string, vector<string> >& queries,const string& required_qid){
    map<string, int> stopwords = read_stopwords();
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
                if (qid!=required_qid){
                  continue;
                }
                string query_lang_string = line.substr(found+1);
                size_t query_string_begin = query_lang_string.find_first_of("(");
                size_t query_string_end = query_lang_string.find_last_of(")");
                // cout<<query_string_begin<<" "<<query_string_end<<endl;
                string query_string = query_lang_string.substr(query_string_begin+1,query_string_end-query_string_begin-8);
                // cout<<qid<<":"<<query_string<<endl;

                istringstream iss(query_string);
                vector<string> tokens;
                vector<string> query_words;

                map<string,int> stem_map;
                copy(istream_iterator<string>(iss),
                     istream_iterator<string>(),
                     back_inserter(tokens));
                for(vector<string>::iterator it = tokens.begin(); it!=tokens.end(); ++it){
                    if((*it).find("0123456789")==string::npos && (*it).find_first_of(".")==string::npos){
                        if(stopwords.find(*it)==stopwords.end()){
                            string stem = r.processTerm(*it);
                            if(stem_map.find(stem)==stem_map.end()){
                                stem_map[stem] = 0;
                                query_words.push_back( stem);

                                words.push_back(stem);
                                // cout<<"push back "<<*it<<endl;
                            }
                        }
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

vector<string> get_query_words(indri::collection::Repository& r, char* query_file,  map<string, vector<string> >& queries){
    map<string, int> stopwords = read_stopwords();
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
                // cout<<query_string_begin<<" "<<query_string_end<<endl;
                string query_string = query_lang_string.substr(query_string_begin+1,query_string_end-query_string_begin-8);
                // cout<<qid<<":"<<query_string<<endl;

                istringstream iss(query_string);
                vector<string> tokens;
                vector<string> query_words;

                map<string,int> stem_map;
                copy(istream_iterator<string>(iss),
                     istream_iterator<string>(),
                     back_inserter(tokens));
                for(vector<string>::iterator it = tokens.begin(); it!=tokens.end(); ++it){
                    if((*it).find("0123456789")==string::npos && (*it).find_first_of(".")==string::npos){
                        if(stopwords.find(*it)==stopwords.end()){
                            string stem = r.processTerm(*it);
                            if(stem_map.find(stem)==stem_map.end()){
                                stem_map[stem] = 0;
                                query_words.push_back( stem);

                                words.push_back(stem);
                                // cout<<"push back "<<*it<<endl;
                            }
                        }
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

int get_df_from_stem(indri::collection::Repository& r, const string& stem){
    indri::server::LocalQueryServer local(r);
    
    return local.documentStemCount(stem);
}

float get_avdl(indri::collection::Repository& r){
  indri::server::LocalQueryServer local(r);
  UINT64 termCount = local.termCount();
  UINT64 docCount = local.documentCount();
  return termCount*1.0/docCount;
}