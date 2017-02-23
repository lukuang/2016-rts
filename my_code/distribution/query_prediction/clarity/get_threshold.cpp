#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/QueryEnvironment.hpp"
#include <cmath>
#include "indri/Parameters.hpp"
#include "indri/RelevanceModel.hpp"
#include <iostream>
#include <typeinfo>
#include <algorithm>
#include <map>
#include <fstream>
using namespace std;


void open_index(indri::api::QueryEnvironment& environment, string& rep_name){
    environment.addIndex(rep_name);
}

vector<string> get_terms(indri::collection::Repository& r){
  indri::collection::Repository::index_state state = r.indexes();
  vector<string> terms ;

  indri::index::Index* index = (*state)[0];
  indri::index::VocabularyIterator* iter = index->vocabularyIterator();

  iter->startIteration();

  while( !iter->finished() ) {
    indri::index::DiskTermData* entry = iter->currentEntry();
    indri::index::TermData* termData = entry->termData;
    if (termData->corpus.documentCount>=100){
        //std::cout << termData->term << " "
        //      << termData->corpus.documentCount <<  std::endl;
        terms.push_back(termData->term);
    }
    iter->nextEntry();
  }

  delete iter;
  return terms;

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


int main(int argc, char** argv){
    indri::collection::Repository r;
    string rep_name = argv[1];
    std::vector <float> term_clarity;
    //string term = argv[2];
    /*get terms with DF higher than 100*/
    r.openRead( rep_name );
    vector<string> candidate_terms = get_terms(r);
    r.close();

    /*compute the clarity threshold(higher than 80% of the single term queries)*/
    int documents = 5;
    int terms = 10;
    int maxGrams = 1;
    string rmSmoothing = "method:f2exp,s:0.1";
    indri::api::QueryEnvironment environment;
    open_index(environment,rep_name);
    for(int i=0; i<candidate_terms.size();i++){
        indri::query::RelevanceModel model( environment, rmSmoothing, maxGrams, documents );
        model.generate(candidate_terms[i]);
        const std::vector<indri::query::RelevanceModel::Gram*>& grams = model.getGrams();
        term_clarity.push_back( clarity(candidate_terms[i],environment, grams, terms) );
    }
    sort(term_clarity.begin(),term_clarity.end());
    size_t size = term_clarity.size();
    size_t needed = int(term_clarity.size()*0.8);
    float threshold = term_clarity[int(term_clarity.size()*0.8)];
    cout<<"size: "<<size<<" needed: "<<needed<<endl;
    cout<<"first: "<<term_clarity[0]<<" last"<<term_clarity[size-1]<<endl;
    cout<<"the threshold is "<<threshold<<endl;
}