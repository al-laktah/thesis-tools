from difflib import Differ, SequenceMatcher
from tokenizers import tokenize_into_paragraphs, tokenize_into_sentences, tokenize_into_words
import diff_match_patch as dmp_module

def find_paragraphs_diff(paragraphs_list_1, paragraphs_list_2):
    d = Differ()
    diff = d.compare(paragraphs_list_1, paragraphs_list_2)
    return diff

def find_sentences_diff(sentences_list_1, sentences_list_2):
    d = Differ()
    diff = d.compare(sentences_list_1, sentences_list_2)
    return diff

def find_words_diff(words_list_1, words_list_2):
    d = Differ()
    diff = d.compare(words_list_1, words_list_2)
    return diff

def diff_report(report_1, report_2, paragraph_diff=False, sentence_diff=False, word_diff=False):
    def paragrahps_report(report_1, report_2):
        paragraphs_list_1 = tokenize_into_paragraphs(report_1)
        paragraphs_list_2 = tokenize_into_paragraphs(report_2)
        
        paragraphs_diff = find_paragraphs_diff(paragraphs_list_1, paragraphs_list_2)
        
        print("Paragraphs diff:")
        print("\n".join(paragraphs_diff))
    
    def sentences_report(report_1, report_2):
        sentences_list_1 = tokenize_into_sentences(report_1)
        sentences_list_2 = tokenize_into_sentences(report_2)
        
        sentences_diff = []
        for paragraph_1, paragraph_2 in zip(sentences_list_1, sentences_list_2):
            sentences_diff.append(find_sentences_diff(paragraph_1, paragraph_2))
        
        print("\n\nDiffrences in Sentences per Paragraph:")
        for i, diff in enumerate(sentences_diff):
            print(f"Paragraph {i+1}:")
            print("\n".join(diff))
    
    def words_report(report_1, report_2):
        words_list_1 = tokenize_into_words(report_1)
        words_list_2 = tokenize_into_words(report_2)
        
        words_diff = []
        for paragraph_1, paragraph_2 in zip(words_list_1, words_list_2):
            par_diff = []
            for sentence_1, sentence_2 in zip(paragraph_1, paragraph_2):
                par_diff.append(find_words_diff(sentence_1, sentence_2))
            words_diff.append(par_diff)
        
        print("\n\nDiffrences in Words per Sentences per Paragraph:")
        for i, par_diff in enumerate(words_diff):
            print(f"Paragraph {i+1}:")
            for j, sentence_diff in enumerate(par_diff):
                print(f"Sentence {j+1}:")
                print("\n".join(sentence_diff))

    if paragraph_diff:
        paragrahps_report(report_1, report_2)
    if sentence_diff:
        sentences_report(report_1, report_2)
    if word_diff:
        words_report(report_1, report_2)
    if not any([paragraph_diff, sentence_diff, word_diff]):
        paragrahps_report(report_1, report_2)
        sentences_report(report_1, report_2)
        words_report(report_1, report_2)

def sm_similarity_ratio(report_1, report_2, paragraphs=False, Sentences=False):
    ratio_dict = dict()

    ratio_dict['report_similarity'] = SequenceMatcher(None, report_1, report_2).ratio()

    if paragraphs:
        report_1_paragraphs = tokenize_into_paragraphs(report_1)
        report_2_paragraphs = tokenize_into_paragraphs(report_2)
        ratio_dict['paragraph_similarity'] = []
        for (paragraph_1, paragraph_2) in zip(report_1_paragraphs, report_2_paragraphs):
            ratio_dict['paragraph_similarity'].append(SequenceMatcher(None, paragraph_1, paragraph_2).ratio())

    if Sentences:
        report_1_sentences = tokenize_into_sentences(report_1, flatten=True)
        report_2_sentences = tokenize_into_sentences(report_2, flatten=True)
        ratio_dict['sentence_similarity'] = []
        for sentence_1, sentence_2 in zip(report_1_sentences, report_2_sentences):
            ratio_dict['sentence_similarity'].append(SequenceMatcher(None, sentence_1, sentence_2).ratio())

    return ratio_dict

def levenshtein_distance(report_1, report_2, paragraphs=False, Sentences=False):
    dmp = dmp_module.diff_match_patch()
    distance_dict = dict()
    report_distance = dmp.diff_levenshtein(dmp.diff_main(report_1, report_2))
    distance_dict['report_distance'] = (report_distance, report_distance/max(len(report_1), len(report_2)))

    if paragraphs:
        report_1_paragraphs = tokenize_into_paragraphs(report_1)
        report_2_paragraphs = tokenize_into_paragraphs(report_2)
        distance_dict['paragraph_distance'] = []
        for (paragraph_1, paragraph_2) in zip(report_1_paragraphs, report_2_paragraphs):
            paragraph_distance = dmp.diff_levenshtein(dmp.diff_main(paragraph_1, paragraph_2))
            distance_dict['paragraph_distance'].append(((paragraph_distance, paragraph_distance/max(len(paragraph_1), len(paragraph_2)))))

    if Sentences:
        report_1_sentences = tokenize_into_sentences(report_1, flatten=True)
        report_2_sentences = tokenize_into_sentences(report_2, flatten=True)
        distance_dict['sentence_distance'] = []
        for sentence_1, sentence_2 in zip(report_1_sentences, report_2_sentences):
            sentence_distance = dmp.diff_levenshtein(dmp.diff_main(sentence_1, sentence_2))
            distance_dict['sentence_distance'].append((sentence_distance, sentence_distance/max(len(sentence_1), len(sentence_2))))

    return distance_dict