#include "indri/Parameters.hpp"
#include "indri/RelevanceModel.hpp"
#include <iostream>
#include <typeinfo>
#include <algorithm>
#include <map>
#include <cmath>
#include <fstream>
using namespace std;

void open_index(indri::api::QueryEnvironment& environment, string& rep_name){
    environment.addIndex(rep_name);
}

static double clarity( const std::string& query,
                       indri::api::QueryEnvironment & env,
                       const std::vector<indri::query::RelevanceModel::Gram*>& grams, int numTerms ) {

  int count = 0;
  double sum=0, ln_Pr=0;
  for( size_t j=0; j< numTerms && j < grams.size(); j++ ) {
    std::string t = grams[j]->terms[0];
    count++;
    // query-clarity = SUM_w{P(w|Q)*log(P(w|Q)/P(w))}
    // P(w)=cf(w)/|C|
    // the relevance model uses stemmed terms, so use stemCount
    double pw = ((double)env.stemCount(t)/(double)env.termCount());
    // P(w|Q) is a prob computed by any model, e.g. relevance models
    double pwq = grams[j]->weight;
    sum += pwq;
    ln_Pr += (pwq)*log(pwq/pw);
  }
  return (ln_Pr/(sum ? sum : 1.0)/log(2.0));
}

map<string,string> get_queries(char* query_file){
    ifstream f;
    string line;
    map<string,string> queries;
    string qid="";
    bool is_text = false;
    f.open(query_file);
    if(f.is_open()){
        while(getline(f,line)){
            if ((line.find(":"))!=string::npos){
                size_t found = line.find(":");
                qid  = line.substr(0,found);
                queries[qid] = line.substr(found+1);
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
    return queries;
}

int main(int argc, char** argv){
    indri::collection::Repository r;
    string rep_name = argv[1];
    float term_clarity;
    map<string, float> clarity_map;
    vector<string> result;
    float threshold = atof(argv[2]);
    char* query_file =  argv[3];
    int documents = 5;
    int terms = 10;
    int maxGrams = 1;
    string rmSmoothing = "method:f2exp,s:0.1";
    indri::api::QueryEnvironment environment;
    open_index(environment,rep_name);
    /*get terms with DF higher than 100*/
    map<string,string> queries = get_queries(query_file);
    map<float, string> score_id_map;
    float highest_score = -1000;
    for(map<string,string>:: iterator it=queries.begin(); it!=queries.end(); ++it){
        //cout<<"qid: "<<it->first<<" text: "<<it->second<<endl;
        indri::query::RelevanceModel model( environment, rmSmoothing, maxGrams, documents );
        model.generate(it->second);
        const std::vector<indri::query::RelevanceModel::Gram*>& grams = model.getGrams();
        term_clarity =clarity(it->second,environment, grams, terms);
        clarity_map[it->first] = term_clarity;
        if (term_clarity>highest_score){
            highest_score = term_clarity;
        }
        score_id_map[term_clarity] = it->first;
        //cout<<"qid: "<<it->first<<" text: "<<it->second<<"\tclarity: "<<term_clarity<<endl;
        if(result.size()==0){
            result.push_back(it->first);
        }
    }
    if(result.size()==0){
        result.push_back(score_id_map[highest_score]);
    }
    cout<<"needed queries"<<endl;
    for(int j=0; j<result.size(); j++){
        cout<<result[j]<<" "<<clarity_map[result[j]]<<endl;
    }
}
