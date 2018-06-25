import logging
from timeit import default_timer as timer
import os
import sys
import pandas as pd
import csv
from nltk.corpus import wordnet as wn
from nltk.wsd import lesk
import pywsd.lesk as pylesk
import ast
import nltk

semcor_ic = nltk.corpus.wordnet_ic.ic('ic-semcor.dat')

def open_file(file, type):
    if type == "warriner":
        logging.debug("Entering open file warriner")
        raw_table = pd.read_csv(file, sep=',', encoding='utf-8')
    else:
        logging.debug("Entering open file pandas")
        raw_table = pd.read_csv(file, sep=';', encoding='utf-8')
    # This transforms the csv-string back to a list
        raw_table['aspect'] = raw_table['aspect'].map(ast.literal_eval)
        raw_table['opinion'] = raw_table['opinion'].map(ast.literal_eval)
        raw_table['opinion_tags'] = raw_table['opinion_tags'].map(ast.literal_eval)
        raw_table['aspect_tags'] = raw_table['aspect_tags'].map(ast.literal_eval)
        raw_table['original_lemmas'] = raw_table['original_lemmas'].map(ast.literal_eval)
    return raw_table


def save_file(file, name):
    logging.debug("Entering writing pandas to file")
    try:
        filepath = "./save/"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        file.to_csv(filepath + name + ".csv", encoding='utf-8', sep=";", quoting=csv.QUOTE_NONNUMERIC)
        print("Saved file: %s%s%s" % (filepath, name, ".csv"))
    except IOError as exception:
        print("Couldn't save the file. Encountered an error: %s" % exception)
    logging.debug("Finished writing: " + name)


def return_sys_arguments(args):
    if len(args) == 2:
        return args[1]
    else:
        return None


def read_folder_contents(path_to_files):
    filelist = os.listdir(path_to_files)
    return filelist


def find_synonyms(raw_df):
    # This defines the lists that are sent to the wordnet synonym search
    lists_of_words = ["aspect_tags"]
    list_of_list_of_synonyms = []
    for i, phrase in enumerate(df["aspect"]):
        list_of_synonyms = []
        for words in lists_of_words:
            if len(df[words][i]) != 0:
                k = 0
                while k < len(df[words][i]):
                    name = df[words][i][k][0]
                    wn_tag = find_wordnet_pos(df[words][i][k][1])
                    find_wordnet_synonyms(name, wn_tag)
                    k+=1

def find_wordnet_synonyms(word, pos_tag):
    """This finds the synonyms from wordnet and calculates their similarity."""
    if pos_tag is not None:
        original_words = wn.synsets(word, pos_tag)
    if len(original_words) != 0:
        # print(original_word[0])
        print("Original synset")
        # Synsets are built by grouping synonyms
        # together.
        for similar in original_words:
            print("Original: %s similar: %s similarity %s" % (original_words[0], similar, original_words[0].wup_similarity(similar)))
        print("Hyponyms")
        # Hyponym is a more specific version of the word. E.g. mouse's hyponym
        # can be field_mouse
        for word in original_words:
            # Makes no sense to calculate this with path, as it's always 0.5 due to their distance
            for hypowords in word.hyponyms():
                print("Original: %s hyponym: %s similarity %s" % (word, hypowords, word.wup_similarity(hypowords)))
            print("Original: %s hyponyms: %s" % (word, word.hyponyms()))
        print("Hypernyms")
        # Hypernym is a more generic term for the word. E.g. mouse's hypernym
        # is a rodent.
        for word in original_words:
            for hypewords in word.hypernyms():
                print("Original: %s hypernym: %s similarity %s" % (word, hypewords, word.wup_similarity(hypewords)))
            print("Original: %s hypernym: %s" % (word, word.hypernyms()))
        print("Similar to")
        # This only works with adjectives, as nouns do not have such relations
        for word in original_words:
            # This gives always None as similarity.
            # for similar_words in word.similar_tos():
            #     print("Original: %s similar: %s similarity %s" % (word, similar_words, word.path_similarity(similar_words)))
            print("Original: %s similar_to: %s" % (word, word.similar_tos()))

def find_wordnet_pos(pos_tag):
    """This finds and returns the Wordnet version of a POS tag that is given to it."""
    if pos_tag == "NN":
        return wn.NOUN
    elif pos_tag == "JJ":
        return wn.ADJ
    elif pos_tag == "RB":
        return wn.ADV
    elif pos_tag == "VB":
        return wn.VERB
    else:
        # If the word is not found, it is assumed to be a noun.
        return wn.NOUN


def wsd_pywsd_adapted_lesk(raw_df):
    """This finds the synset of the word using
        the original sentence as context and the
        simple lesk algorithm from pywsd-package."""
    tokenized_sentences = raw_df["original_text"]
    aspect_words = raw_df["aspect_tags"]
    for i, phrase in enumerate(aspect_words):
        for word in phrase:
            aspect = None
            wn_check = []
            wn_check = wn.synsets(word[0], pos=find_wordnet_pos(word[1]))
            if len(wn_check) > 0:
                aspect = pylesk.adapted_lesk(tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
            print("Aspect word: %s" % (word[0]))
            if aspect is not None:
                print("Adapted %s, Definition: %s" % (aspect, aspect.definition()))
            print(tokenized_sentences[i])
    opinion_words = raw_df["opinion_tags"]
    for i, phrase in enumerate(opinion_words):
        for word in phrase:
            opinion = pylesk.adapted_lesk(tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
            print(tokenized_sentences[i])
            if opinion is not None:
                print("Adapted %s, Definition: %s" % (opinion, opinion.definition()))


def wsd_pywsd_simple_lesk(raw_df):
    """This finds the synset of the word using
        the original sentence as context and the
        simple lesk algorithm from pywsd-package."""
    tokenized_sentences = raw_df["original_text"]
    aspect_words = raw_df["aspect_tags"]
    for i, phrase in enumerate(aspect_words):
        for word in phrase:
            aspect = None
            wn_check = []
            wn_check = wn.synsets(word[0], pos=find_wordnet_pos(word[1]))
            if len(wn_check) > 0:
                aspect = pylesk.simple_lesk(tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
            print("Aspect word: %s" % (word[0]))
            if aspect is not None:
                print("Simple %s, Definition: %s" % (aspect, aspect.definition()))
            print(tokenized_sentences[i])
    opinion_words = raw_df["opinion_tags"]
    for i, phrase in enumerate(opinion_words):
        for word in phrase:
            opinion = pylesk.simple_lesk(tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
            print(tokenized_sentences[i])
            if opinion is not None:
                print("Simple %s, Definition: %s" % (opinion, opinion.definition()))
    # Not finished yet on what to return

def wsd_nltk_lesk(raw_df):
    """This finds the synset of the word using
        the original sentence as context and the
        original lesk algorithm from nltk-package."""
    df = raw_df
    full_aspect_synset_list = []
    full_aspect_synset_list_definition = []
    aspect_synset_list_definition = []
    aspect_synset_list = []
    opinion_synset_list = []
    opinion_synset_list_definition = []
    full_opinion_synset_list = []
    full_opinion_synset_list_definition = []
    aspect_opinion = ["aspect_tags", "opinion_tags"]
    tokenized_sentences = raw_df["tokenized_sentence"]
    aspect_words = raw_df["aspect_tags"]

    for opinion_list in aspect_opinion:
        for i, phrase in enumerate(df[opinion_list]):
            for word in phrase:
                aspect = lesk(tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
                if aspect is not None:
                    if opinion_list is "aspect_tags":
                        aspect_synset_list.append(aspect)
                        aspect_synset_list_definition.append(aspect.definition())
                    else:
                        opinion_synset_list.append(aspect)
                        opinion_synset_list_definition.append(aspect.definition())
            if opinion_list is "aspect_tags":
                full_aspect_synset_list.append(aspect_synset_list)
                full_aspect_synset_list_definition.append(aspect_synset_list_definition)
                aspect_synset_list = []
                aspect_synset_list_definition = []
            else:
                full_opinion_synset_list.append(opinion_synset_list)
                full_opinion_synset_list_definition.append(opinion_synset_list_definition)
                opinion_synset_list = []
                opinion_synset_list_definition = []
    df_aspect_list = pd.Series(full_aspect_synset_list)
    df_aspect_definition_list = pd.Series(full_aspect_synset_list_definition)
    df["nltk_lesk_aspect_synset"] = df_aspect_list.values
    df["nltk_lesk_aspect_definition"] = df_aspect_definition_list.values
    df["nltk_lesk_opinion_synset"] = pd.Series(full_opinion_synset_list).values
    df["nltk_lesk_opinion_definition"] = pd.Series(full_opinion_synset_list_definition).values
    return df


def tokenize_sentences(raw_df):
    """This tokenizes the sentences, with
    every word being a token from a sentence."""
    start = timer()
    df = raw_df
    spacy_tagged_sentence = df["original_lemmas"]
    tokenized_sentences = []
    sentence = []
    for i, phrase in enumerate(df["aspect"]):
        for words in spacy_tagged_sentence[i]:
            if len(words) != 0:
                sentence.append(words[0])
        tokenized_sentences.append(sentence)
        sentence = []
    tokenized_series = pd.Series(tokenized_sentences)
    df["tokenized_sentence"] = tokenized_series.values
    end = timer()
    logging.debug("Time: %.2f seconds" % (end - start))
    return df


def main(raw_df, name):
    logging.debug("Entering main")
    df = raw_df
    df = tokenize_sentences(df)
    df = wsd_nltk_lesk(df)
    save_file(df, name + "_WORDNET_WSD")
    # wsd_pywsd_simple_lesk(df)
    # wsd_pywsd_adapted_lesk(df)
    # find_synonyms(df)

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.debug("Wordnet version: %s" % wn.get_version())
    logging.debug("Wordnet adjective: %s" % wn.ADJ)
    logging.debug("Wordnet verb: %s" % wn.VERB)
    logging.debug("Wordnet noun: %s" % wn.NOUN)
    logging.debug("Wordnet adverb: %s" % wn.ADV)

    argument = return_sys_arguments(sys.argv)
    if argument is None:
        print("You didn't give an argument")
    elif os.path.isdir(argument):
        files = read_folder_contents(argument)
        print("Gave a folder: %s, that has %s files." % (argument, str(len(files))))
        x = 0
        for f in files:
            x += 1
            df = open_file(argument + "/" + f, "pandas")
            name = os.path.splitext(f)[0]
            print("Opened file: %s" % name)
            main(df, name)

    elif os.path.isfile(argument):
        df = open_file(argument, "pandas")
        name = os.path.splitext(argument)[0]
        main(df, name)

    else:
        print("You didn't give a file or folder as your argument.")