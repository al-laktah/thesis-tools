from typing import Union, List, Dict
from nltk import word_tokenize, sent_tokenize
from itertools import chain

def _flatten(list_of_lists: List[List]) -> List:
    return list(chain(*list_of_lists))


def _split_into_lines(report):
    return report.split("\n")


def tokenize_into_paragraphs(report, dictionary: bool = False) -> Union[List, Dict]:
    lines = _split_into_lines(report)
    paragraphs_list = list(filter(None, lines))
    if dictionary:
        return {
            f"Paragraph {i+1}": paragraph.strip()
            for i, paragraph in enumerate(paragraphs_list) 
            if paragraph
        }
    else:
        return paragraphs_list


def tokenize_into_sentences(
    report, dictionary: bool = False, flatten: bool = False, language: str = "german"
) -> Union[List, Dict]:
    if dictionary:
        sentences_dict = {}
        paragraphs_dict = tokenize_into_paragraphs(report, dictionary=True)
        for key, paragraph in paragraphs_dict.items():
            sentences_dict[key] = {
                f"sentence {i+1}": sentence
                for i, sentence in enumerate(
                    sent_tokenize(paragraph, language=language)
                )
            }
        return sentences_dict
    else:
        paragraphs = tokenize_into_paragraphs(report)
        sentences_list = [
            sent_tokenize(paragraph, language=language) for paragraph in paragraphs
        ]
        if flatten:
            return _flatten(sentences_list)
        else:
            return sentences_list


def tokenize_into_words(
    report, dictionary: bool = False, flatten: bool = False, language: str = "german"
) -> Union[List, Dict]:
    if dictionary:
        setences_dict = tokenize_into_sentences(
            report, dictionary=True, language=language
        )
        words_dict = dict()
        for key, paragraph_dict in setences_dict.items():
            par_dict = dict()
            for sentence_key, sentence in paragraph_dict.items():
                par_dict[sentence_key] = word_tokenize(sentence, language=language)
            words_dict[key] = par_dict
        return words_dict
    else:
        sentences = tokenize_into_sentences(report, language=language)
        words_list = []
        for paragraph in sentences:
            par_list = []
            for sentence in paragraph:
                par_list.append(word_tokenize(sentence, language=language))
            words_list.append(par_list)
        if flatten:
            return _flatten(_flatten(words_list))
        else:
            return words_list
