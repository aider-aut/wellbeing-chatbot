import re
import numpy as np
import pandas as pd
from pprint import pprint
import pyLDAvis
import pyLDAvis.gensim
import matplotlib.pyplot as plt
import gensim
from gensim import corpora
from gensim.models import CoherenceModel
from gensim.utils import simple_preprocess
import spacy
from nltk.corpus import stopwords

with open('landbot_statements.txt', 'r') as f:
    documents = f.readlines()
    stop_words = stopwords.words('english')
    stop_words.extend(['pc', 'el', 'rf', 'rp', 'd', 'f', 'gs', 'm', 'mr', 'redo', 'rw', 'fb', 'feel', 'want', "also", "thing", "year",
                       'make', 'get', 'time', 'sometimes', 'go', 'really', 'can', 'lot', 'day', "try", "much", "do", "see", "anything", "situation", "say"])


def sent_to_words(sentences):
    for sentence in sentences:
        # deacc=True removes punctuations
        yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))


def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]


def make_bigrams(texts):
    return [bigram_mod[doc] for doc in texts]


def make_trigrams(texts):
    return [trigram_mod[bigram_mod[doc]] for doc in texts]


data_words = list(sent_to_words(documents))
data_words_nostops = remove_stopwords(data_words)
# higher threshold fewer phrases.
bigram = gensim.models.Phrases(data_words_nostops, min_count=1, threshold=1)
trigram = gensim.models.Phrases(bigram[data_words_nostops], threshold=1)
bigram_mod = gensim.models.phrases.Phraser(bigram)
trigram_mod = gensim.models.phrases.Phraser(trigram)


def lemmatization(texts, allowed_postags=['NOUN', 'ADJ']):
    """https://spacy.io/api/annotation"""
    texts_out = []
    for sent in texts:
        doc = nlp(" ".join(sent))
        texts_out.append(
            [token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out


data_words_bigrams = make_bigrams(data_words_nostops)
nlp = spacy.load('en_core_web_md', disable=['parser', 'ner'])
data_lemmatized = lemmatization(
    data_words_bigrams, allowed_postags=['NOUN', 'ADJ'])
id2word = corpora.Dictionary(data_lemmatized)
texts = data_lemmatized
corpus = [id2word.doc2bow(text) for text in texts]

lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                            id2word=id2word,
                                            num_topics=3,
                                            random_state=100,
                                            update_every=1,
                                            chunksize=100,
                                            passes=10,
                                            alpha='auto',
                                            per_word_topics=True)
pprint(lda_model.print_topics())
doc_lda = lda_model[corpus]
# a measure of how good the model is. lower the better.
print('\nPerplexity: ', lda_model.log_perplexity(corpus))

# Compute Coherence Score
coherence_model_lda = CoherenceModel(
    model=lda_model, texts=data_lemmatized, dictionary=id2word, coherence='c_v')
coherence_lda = coherence_model_lda.get_coherence()
print('\nCoherence Score: ', coherence_lda)

# Visualize the topics
vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word)
pyLDAvis.show(vis, ip='0.0.0.0', port=8021, open_browser=False)
