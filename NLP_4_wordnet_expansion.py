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
    lists_of_words = ["nltk_lesk_aspect_synset"]
    list_of_list_of_synonyms = []
    for i, phrase in enumerate(df["aspect"]):
        list_of_synonyms = []
        for words in lists_of_words:
            if len(df[words][i]) != 0:
                k = 0
                while k < len(df[words][i]):
                    synonyms = find_wordnet_synonyms_nouns(df[words][i][k])
                    k += 1
            #     k = 0
                # while k < len(df[words][i]):
                #     name = df[words][i][k][0]
                #     wn_tag = find_wordnet_pos(df[words][i][k][1])
                #     find_wordnet_synonyms(name, wn_tag)
                #     k+=1


def find_wordnet_synonyms_nouns(noun_synset):
    original_synset = noun_synset
    synonym_words = []
    print("Original: %s" % (original_synset))

    # This is for the synonym words from this exact synset.
    for synonym_word in original_synset.lemmas():
        print("Original: %s synonym: %s" % (
        original_synset, synonym_word))

    # This is for the synonym synsets that compare
    # against the original synset.
    for synonym_synset in wn.synsets(original_synset.lemma_names()[0], original_synset.pos()):
        # print(synonym)
        if (original_synset != synonym_synset) and (original_synset.lch_similarity(synonym_synset) >= 2):
            if synonym_synset.lemma_names()[0] not in synonym_words:
                synonym_words.append(synonym_synset.lemma_names()[0])
            print("Original: %s other synsets: %s LCH-similarity %s" % (
                original_synset, synonym_synset, original_synset.lch_similarity(synonym_synset)))
            if original_synset.pos() == "n":
                for nested_hyponym_synset in synonym_synset.hyponyms():
                    if original_synset.lch_similarity(nested_hyponym_synset) >= 2:
                        print("Other synset: %s nested_hyponym words: %s LCH(original) %s" % (synonym_synset, nested_hyponym_synset, original_synset.lch_similarity(nested_hyponym_synset)))
                        # Here has to append also to the synonym_words-list.

                        # This goes into the hyponyms of hyponyms, seems too deep for now.
                        # for double_nested_hyponym_synset in nested_hyponym_synset.hyponyms():
                        #     print("Hypernym: %s double_nested_hyponym words: %s LCH(original) %s" % (
                        #     nested_hyponym_synset, double_nested_hyponym_synset, original_synset.lch_similarity(double_nested_hyponym_synset)))

                # This iterates first to a higher level, e.g. from Synset computer.n.01
                # to machine.n.01, and then over all the hypernyms from machine.n.01.
                # This doesn't make sense at this level, as it produces too much noise
                # and all the distances are always the same.
                # for hypernym_synset in original_synset.hypernyms():
                #     print("Original: %s nested_hypernym words: %s LCH-similarity %s" % (original_synset, hypernym_synset, original_synset.lch_similarity(hypernym_synset)))
                #     for nested_synonym_synset in hypernym_synset.hyponyms():
                    #     print("Hypernym: %s nested_synonym synset: %s LCH (original&nested) %s" % (hypernym_synset, nested_synonym_synset, original_synset.lch_similarity(nested_synonym_synset)))
        # print("Original: %s other synset words: %s WUP-similarity %s" % (
        #     original_synset, synonym_synset, original_synset.wup_similarity(synonym_synset)))

    # This part deals with adjectives, that
    # have different relations than nouns.
    if original_synset.pos() == "a":

        # This is for antonyms (opposites e.g. dry-wet), it
        # loops through all synonyms, although antonym seems
        # to be assigned only to the first for the set.
        for synonym in original_synset.lemmas():
            for antonym in synonym.antonyms():
                print("Original: %s antonym: %s" % (
                    synonym, antonym))

        # This is for similar adjectives, which are
        # also called satellites:
        # https://wordnet.princeton.edu/documentation/wngloss7wn
        for similar in original_synset.similar_tos():
            print("Original: %s satellite_adjective: %s" % (
                original_synset, similar))
    return synonym_words


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


def wsd_lesk(raw_df, algorithm_choice):
    """This finds the synset of the word using
        the original sentence as context and
        different lesk algorithms from nltk-
        and pywsd-packages.

        Algorithm choices are: 1. nltk's lesk
        2. pywsd simple_lesk, 3. pywsd advanced_lesk."""
    start = timer()
    algorithm_dict = {1: "nltk_lesk", 2: "pywsd_simple_lesk",
                      3: "pywsd_advanced_lesk", 4: "pywsd_cosine_lesk"}
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
    non_tokenized_sentences = raw_df["original_text"]

    for opinion_list in aspect_opinion:
        for i, phrase in enumerate(df[opinion_list]):
            multiple_word_found = False
            for j, word in enumerate(phrase):
                if multiple_word_found is False:
                    aspect = None
                    wn_check = []
                    if len(phrase) >= 2:
                        k = 0
                        temporary_combined_word = []
                        while k < len(phrase):
                            temporary_combined_word.append(phrase[k][0])
                            k += 1
                        combined_word_string = '_'.join(temporary_combined_word)
                        wn_check = wn.synsets(combined_word_string, pos=find_wordnet_pos(word[k][1]))
                        multiple_word_found = True
                    if len(wn_check) == 0:
                        wn_check = wn.synsets(word[0], pos=find_wordnet_pos(word[1]))
                        multiple_word_found = False
                    if len(wn_check) > 0:
                        if algorithm_choice == 1:
                            if multiple_word_found is True:
                                aspect = lesk(tokenized_sentences[i], combined_word_string, find_wordnet_pos(word[1]))
                            else:
                                aspect = lesk(tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
                        if algorithm_choice == 2:
                            if multiple_word_found is True:
                                aspect = pylesk.simple_lesk(non_tokenized_sentences[i], combined_word_string, find_wordnet_pos(word[1]))
                            else:
                                aspect = pylesk.simple_lesk(non_tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
                        if algorithm_choice == 3:
                            if multiple_word_found is True:
                                aspect = pylesk.adapted_lesk(non_tokenized_sentences[i], combined_word_string,
                                                             find_wordnet_pos(word[1]))
                            else:
                                aspect = pylesk.adapted_lesk(non_tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
                        if algorithm_choice == 4:
                            if multiple_word_found is True:
                                aspect = pylesk.cosine_lesk(non_tokenized_sentences[i], combined_word_string,
                                                            find_wordnet_pos(word[1]))
                            else:
                                aspect = pylesk.cosine_lesk(non_tokenized_sentences[i], word[0], find_wordnet_pos(word[1]))
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
    df[algorithm_dict[algorithm_choice] + "_aspect_synset"] = pd.Series(full_aspect_synset_list).values
    df[algorithm_dict[algorithm_choice] + "_aspect_definition"] = pd.Series(full_aspect_synset_list_definition).values
    df[algorithm_dict[algorithm_choice] + "_opinion_synset"] = pd.Series(full_opinion_synset_list).values
    df[algorithm_dict[algorithm_choice] + "_opinion_definition"] = pd.Series(full_opinion_synset_list_definition).values
    end = timer()
    logging.debug("WSD Lesk Time: %.2f seconds" % (end - start))
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


def reformat_output_file(raw_df):
    df = raw_df.drop(["aspect_v1", "aspect_a1", "aspect_d1", "aspect_v2", "aspect_a2", "aspect_d2",
                              "aspect_v3", "aspect_a3", "aspect_d3", "aspect_v4", "aspect_a4", "aspect_d4",
                              "original_lemmas", "aspect_tags", "opinion_tags", "tokenized_sentence"], axis=1)
    return df


def main(raw_df, name):
    logging.debug("Entering main")
    df = raw_df
    df = tokenize_sentences(df)
    df = wsd_lesk(df, 1)
    df = wsd_lesk(df, 2)
    df = wsd_lesk(df, 3)
    df = wsd_lesk(df, 4)
    find_synonyms(df)

    # df = reformat_output_file(df)
    # save_file(df, name + "_WORDNET_WSD")
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