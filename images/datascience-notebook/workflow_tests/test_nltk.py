import nltk
import pytest

def setup_module(module):
    nltk.download('punkt', download_dir='/tmp/nltk_data')
    nltk.download('punkt_tab', download_dir='/tmp/nltk_data')
    nltk.download('maxent_ne_chunker', download_dir='/tmp/nltk_data')
    nltk.download('words', download_dir='/tmp/nltk_data')
    nltk.download('averaged_perceptron_tagger', download_dir='/tmp/nltk_data')
    nltk.download('averaged_perceptron_tagger_eng', download_dir='/tmp/nltk_data')
    nltk.download('maxent_ne_chunker_tab', download_dir='/tmp/nltk_data')
    nltk.data.path.append('/tmp/nltk_data')

def test_tokenization():
    # Test sentence tokenization
    sentence = "This is a sample sentence. It consists of two sentences."
    tokenized_sentences = nltk.sent_tokenize(sentence)
    assert len(tokenized_sentences) == 2
    assert tokenized_sentences[0] == "This is a sample sentence."
    assert tokenized_sentences[1] == "It consists of two sentences."
    
    # Test word tokenization
    sentence = "The quick brown fox jumps over the lazy dog."
    tokenized_words = nltk.word_tokenize(sentence)
    assert len(tokenized_words) == 10
    assert tokenized_words == ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "."]

def test_stemming():
    # Test Porter stemmer
    porter_stemmer = nltk.PorterStemmer()
    words = ["running", "runs", "ran", "runner"]
    stemmed_words = [porter_stemmer.stem(word) for word in words]
    assert stemmed_words == ["run", "run", "ran", "runner"]
    
    # Test Lancaster stemmer
    lancaster_stemmer = nltk.LancasterStemmer()
    words = ["happiness", "happier", "happiest", "happily"]
    stemmed_words = [lancaster_stemmer.stem(word) for word in words]
    assert stemmed_words == ["happy", "happy", "happiest", "happy"]

def test_named_entity_recognition():
    sentence = "Barack Obama was the 44th President of the United States."
    tokens = nltk.word_tokenize(sentence)
    tags = nltk.pos_tag(tokens)
    ne_chunks = nltk.ne_chunk(tags)

    found_barack_obama = False
    found_united_states = False

    # Buffer for consecutive person tags
    person_buffer = []

    def check_and_clear_buffer():
        nonlocal found_barack_obama
        if person_buffer:
            person_name = " ".join(person_buffer)
            if person_name == "Barack Obama":
                found_barack_obama = True
            person_buffer.clear()

    for ne in ne_chunks:
        if isinstance(ne, nltk.tree.Tree):
            if ne.label() == "PERSON":
                person_buffer.append(" ".join(token[0] for token in ne))
            else:
                # If we encounter a non-PERSON entity, check and clear the buffer
                check_and_clear_buffer()
            if ne.label() == "GPE" and " ".join(token[0] for token in ne) == "United States":
                found_united_states = True
        else:
            # For tokens not recognized as NE, clear the buffer
            check_and_clear_buffer()

    check_and_clear_buffer()

    #print(str(ne_chunks))

    # Assert the named entities were found
    assert found_barack_obama, "Barack Obama as PERSON not found"
    assert found_united_states, "United States as GPE not found"

    # Assert the named entities were found
    assert found_barack_obama, "Barack Obama as PERSON not found"
    assert found_united_states, "United States as GPE not found"