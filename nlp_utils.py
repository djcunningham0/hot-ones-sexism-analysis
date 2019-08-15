import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet


def get_pos_list(tokens):
    """
    Get the simple POS of a word that can be passed into the WordNet lemmatizer. E.g., convert NN to N.
    """
    tag_list = [x[1][0].upper() for x in nltk.pos_tag(tokens)]
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return [tag_dict.get(tag, wordnet.NOUN) for tag in tag_list]


class MyLemmatizer:
    """
    Lemmatize a word using the WordNet lemmatizer and the predicted POS.
    """
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

    def lemmatize(self, word, pos=None):
        """
        Lemmatize a word using the WordNet lemmatizer.
        """
        if pos is None:
            pos = nltk.pos_tag([word])

        return self.lemmatizer.lemmatize(word, pos)

    def stem(self, word, pos=None):
        """
        Same as lemmatize. I'm just adding a stem method so the object can be passed to functions that expect
        a stemmer.
        """
        return self.lemmatize(word, pos)


class MyTokenizer:
    """
    Tokenize a string using the specified tokenizer, stemmer, and other options.
    """
    def __init__(self, tokenizer=None, stemmer=None, replace_pronouns=False, pronoun_token='simple',
                 stopword_list='punctuation'):
        """
        :param tokenizer: a tokenizer to use (e.g., something from nltk.tokenize) (must have a 'tokenize' method)
        :param stemmer: a stemmer or lemmatizer to use (must have a 'stem' method)
        :param replace_pronouns: True to replace gendered pronouns (e.g., he -> he/she)
        :param pronoun_token: 'simple' to replace all gendered pronouns with '<pronoun>' token; 'detailed' to
        replace gendered pronouns with more detail (e.g., 'he/she', 'him/her/his/hers')
        :param stopword_list: list of stop words to remove (defaults to list of most punctuation marks)
        """
        self.tokenizer = tokenizer
        self.stemmer = stemmer
        self.replace_pronouns = replace_pronouns
        if pronoun_token not in ['simple', 'detailed']:
            print("pronoun_token should be 'simple' or 'detailed'. Defaulting to 'simple'")
            self.pronoun_token = 'simple'
        else:
            self.pronoun_token = pronoun_token
        if stopword_list == 'punctuation':
            # note: I'm excluding some punctuation like ! and ? because I think they might be interesting
            self.stopword_list = ['-', '–', '“', '”', '"', "'", '’', '.', ',', ';', ':', '`']
        else:
            self.stopword_list = stopword_list

    def tokenize(self, string):
        """
        Tokenize a string and apply other operations (e.g., stemming, removing stopwords) if specified.
        """
        if self.tokenizer is None:
            tokens = nltk.word_tokenize(string)
        else:
            tokens = self.tokenizer.tokenize(string)

        if self.stopword_list is not None:
            tokens = [t for t in tokens if t not in self.stopword_list]

        if self.replace_pronouns:
            if self.pronoun_token == 'simple':
                pronoun_list = ['he', 'she', "he's", "she's", 'hes', 'shes', "he'd", "she'd", 'him',
                                'his', 'her', 'hers', 'himself', 'herself']
                tokens = ['<pronoun>' if t in pronoun_list else t for t in tokens]
            else:
                tokens = ['<he/she>' if t in ['he', 'she'] else t for t in tokens]
                tokens = ["<he's/she's>" if t in ["he's", "she's"] else t for t in tokens]
                tokens = ['<hes/shes>' if t in ['hes', 'shes'] else t for t in tokens]
                tokens = ["<he'd/she'd>" if t in ["he'd", "she'd"] else t for t in tokens]
                tokens = ['<him/his/her/hers>' if t in ['him', 'his', 'her', 'hers'] else t for t in tokens]
                tokens = ['<himself/herself>' if t in ['himself', 'herself'] else t for t in tokens]

        if self.stemmer is None:
            return tokens
        else:
            pos_list = get_pos_list(tokens)
            stems = [self.stemmer.stem(word, pos) for word, pos in zip(tokens, pos_list)]
            return stems
