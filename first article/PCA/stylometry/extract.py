from __future__ import division
import pytz
import glob

import nltk
from nltk import sent_tokenize, word_tokenize, Text
from nltk.probability import FreqDist
from nltk.corpus import stopwords
import numpy as np
import random

DEFAULT_AUTHOR = "Unknown"

class StyloDocument(object):

    def __init__(self, file_name, author=DEFAULT_AUTHOR):
        self.doc = open(file_name, "r").read()

        self.author = author
        self.file_name = file_name.split(" - ")[1].split(".")[0]
        self.tokens = word_tokenize(self.doc)
        self.text = Text(self.tokens)
        self.fdist = FreqDist(self.text)
        self.sentences = sent_tokenize(self.doc)
        self.sentence_chars = [ len(sent) for sent in self.sentences]
        self.sentence_word_length = [ len(sent.split()) for sent in self.sentences]
        self.paragraphs = [p for p in self.doc.split("\n\n") if len(p) > 0 and not p.isspace()]
        self.paragraph_word_length = [len(p.split()) for p in self.paragraphs]

    
    @classmethod
    def csv_header(cls):
        hebrew_stopwords = stopwords.words('hebrew')
        additional_placeholders = ""
        for word in hebrew_stopwords[:221]:
            additional_placeholders = additional_placeholders + word + ','
        existing_string = "Author,Title,LexicalDiversity,MeanWordLen,MeanSentenceLen,StdevSentenceLen,MeanParagraphLen,DocumentLen,Commas,Semicolons,Quotes,Exclamations,Colons,Dashes,Mdashes,"
        result_string = existing_string + additional_placeholders
        return (result_string)
   

    def term_per_thousand(self, term):
        """
        term       X
        -----  = ------
          N       1000
        """
        return (self.fdist[term] * 1000) / self.fdist.N()

    def mean_sentence_len(self):
        return np.mean(self.sentence_word_length)

    def std_sentence_len(self):
        return np.std(self.sentence_word_length)

    def mean_paragraph_len(self):
        return np.mean(self.paragraph_word_length)
        
    def std_paragraph_len(self):
        return np.std(self.paragraph_word_length)

    def mean_word_len(self):
        words = set(word_tokenize(self.doc))
        word_chars = [ len(word) for word in words]
        return sum(word_chars) /  float(len(word_chars))

    def type_token_ratio(self):
        return (len(set(self.text)) / len(self.text)) * 100

    def unique_words_per_thousand(self):
        # total = 0
        # num_iters = 100
        # for i in range(num_iters):
        #     start = random.randint(0,len(self.text)-1000)
        #     sub_text = self.text[random.randint(0,len(self.text)-1000):]
        #     total += (len(set(sub_text)) / float(len(sub_text)))*100
        # return total/float(num_iters)
        return self.type_token_ratio()/100.0*1000.0 / len(self.text)

    def document_len(self):
        return sum(self.sentence_chars)

    

    def csv_output(self):
        hebrew_stopwords = stopwords.words('hebrew')
        existing_string = '"%s","%s",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g'
        additional_placeholders = ','.join(['%g'] * 221)
        result_string = existing_string + ',' + additional_placeholders

        # Collect all the values that need to be formatted
        values = [
            self.author, 
            self.file_name, 
            self.type_token_ratio(), 
            self.mean_word_len(), 
            self.mean_sentence_len(),
            self.std_sentence_len(),
            self.mean_paragraph_len(), 
            self.document_len(),

            
            self.term_per_thousand(','),
            self.term_per_thousand(';'),
            self.term_per_thousand('"'),
            self.term_per_thousand('!'),
            self.term_per_thousand(':'),
            self.term_per_thousand('-'),
            self.term_per_thousand('--'),
            
        
        ]

        # Add Hebrew stop words
        values.extend(self.term_per_thousand(word) for word in hebrew_stopwords[:221])

        return result_string % tuple(values)
 

    def text_output(self):
        
        hebrew_stopwords = stopwords.words('hebrew')
        print( "##############################################")
        print( "")
        print( "Name: ", self.file_name)
        print( "")

        print( ">>> Phraseology Analysis <<<")
        print( "")
        print( "Lexical diversity        :", self.type_token_ratio())
        print( "Mean Word Length         :", self.mean_word_len())
        print( "Mean Sentence Length     :", self.mean_sentence_len())
        print( "STDEV Sentence Length    :", self.std_sentence_len())
        print( "Mean paragraph Length    :", self.mean_paragraph_len())
        print( "Document Length          :", self.document_len())
        print( "")
        
        print( ">>> Punctuation Analysis (per 1000 tokens) <<<")
        print( "")
        print( 'Commas                   :', self.term_per_thousand(','))
        print( 'Semicolons               :', self.term_per_thousand(';'))
        print( 'Quotations               :', self.term_per_thousand('\"'))
        print( 'Exclamations             :', self.term_per_thousand('!'))
        print( 'Colons                   :', self.term_per_thousand(':'))
        print( 'Hyphens                  :', self.term_per_thousand('-')) # m-dash or n-dash?
        print( 'Double Hyphens           :', self.term_per_thousand('--') )# m-dash or n-dash?
        print( "")

        print( ">>> Lexical Usage Analysis (per 1000 tokens) <<<")
        print( "")
        for i in range(len(hebrew_stopwords)):
            print( hebrew_stopwords[i] + "               :" , self.term_per_thousand(hebrew_stopwords[i]))
        
       


class StyloCorpus(object):

    
    def __init__(self,documents_by_author):
        self.documents_by_author = documents_by_author

    @classmethod
    def from_path_list(cls, path_list, author=DEFAULT_AUTHOR):
        stylodoc_list = cls.convert_paths_to_stylodocs(path_list)
        documents_by_author = {author:stylodoc_list}
        return cls(documents_by_author)

    @classmethod
    def from_stylodoc_list(cls, stylodoc_list, author=DEFAULT_AUTHOR):
        author = DEFAULT_AUTHOR
        documents_by_author = {author:stylodoc_list}
        return cls(documents_by_author)

    @classmethod
    def from_documents_by_author(cls, documents_by_author):
        return cls(documents_by_author)

    @classmethod
    def from_paths_by_author(cls, paths_by_author):
        documents_by_author = {}
        for author, path_list in paths_by_author.iteritems():
            documents_by_author[author] = cls.convert_paths_to_stylodocs(path_list,author)
        return cls(documents_by_author)

    @classmethod
    def from_glob_pattern(cls, pattern):
        documents_by_author = {}
        if isinstance(pattern,list):
            for p in pattern:
                documents_by_author.update(cls.get_dictionary_from_glob(p))
        else:
            documents_by_author = cls.get_dictionary_from_glob(pattern)
        return cls(documents_by_author)

    @classmethod
    def convert_paths_to_stylodocs(cls, path_list, author=DEFAULT_AUTHOR):
        stylodoc_list = []
        for path in path_list:
            sd = StyloDocument(path, author)
            stylodoc_list.append(sd)
        return stylodoc_list

    @classmethod
    def get_dictionary_from_glob(cls, pattern):
        documents_by_author = {}
        for path in glob.glob(pattern):
            author = path.split("\\")[-1].split(" - ")[0]
            document = StyloDocument(path, author)
            if author not in documents_by_author:
                documents_by_author[author] = [document]
            else:
                documents_by_author[author].append(document)
        return documents_by_author

    def output_csv(self, out_file, author=None):
        print(out_file)
        csv_data = StyloDocument.csv_header() + '\n'
        if not author:
            for a in self.documents_by_author.keys():
                for doc in self.documents_by_author[a]:
                    csv_data += doc.csv_output() + '\n'
        else:
            for doc in self.documents_by_author[author]:
                csv_data += doc.csv_output() + '\n'
        if out_file:
            with open(out_file,'w') as f:
                f.write(csv_data)
        return csv_data
            
