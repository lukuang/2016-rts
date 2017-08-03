"""
Utilities for vectors
"""

import os
import json
import sys
import re
import argparse
import codecs
import numpy as np
from scipy.spatial.distance import cosine
import gensim
from enum import IntEnum, unique
from nltk.corpus import stopwords

@unique
class ModelType(IntEnum):
    glove = 0
    word2vec = 1



def load_glove_model(model_file):
    # print "Loading Glove Model"
    f = open(model_file,'r')
    model = {}
    for line in f:
        splitLine = line.split()
        word = splitLine[0]
        embedding = np.array([float(val) for val in splitLine[1:]])
        model[word] = embedding
    # print "Done.",len(model)," words loaded!"
    dimension = len(model.values()[0])
    return model,dimension

def load_word2vec_model(model_file):
    model = gensim.models.KeyedVectors.load_word2vec_format(model_file, binary=True)
    dimension = model.vector_size
    return model,dimension

class EmbeddingModel(object):
    """
    base class for models
    """

    def __init__(self,model_file,model_type):
        self._model_type = model_type
        if model_type ==  ModelType.glove:
            self._model, self._dimension = load_glove_model(model_file)
        elif model_type == ModelType.word2vec:
            self._model, self._dimension = load_word2vec_model(model_file)
        self._stopwords = nltk.corpus.stopwords.words('english')
        self._missing_words = set()
        self._total_words = set()

    def get_sentence_vector(sentence):
        sentence_vector = np.array([.0]*300)
        for w in sentence:
            if w not in self._stopwords:
                self._total_words.add(w)
                try:
                    sentence_vector += self._model[w]
                except KeyError:
                    self._missing_words.add(w)

        return sentence_vector

    def similarity(sentence_vector1,sentence_vector2):
        return 1 - cosine(sentence_vector1,sentence_vector2)




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("")
    args=parser.parse_args()



if __name__=="__main__":
    main()

