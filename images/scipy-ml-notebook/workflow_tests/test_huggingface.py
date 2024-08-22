### THESE TESTS WILL DOWNLOAD A BUNCH OF MODELS TO YOUR .CACHE DIR
### IF MANUALLY RUN, DELETE THEM AFTER TO SAVE SPACE

# The results of these tests are somewhat subject to randomness. It's possible that values will change as models change. You can always run these from the container to see what's wrong with them.

from transformers import pipeline
from transformers import AutoTokenizer

import pytest

# test basic sentiment analysis
def get_sentiment_analysis(string):
    return pipeline("sentiment-analysis")(string)

def test_positive_sent():
    sent = get_sentiment_analysis("I love you")[0]
    assert sent["label"] == "POSITIVE"
    assert sent["score"] > .9
    
def test_negative_sent():
    sent = get_sentiment_analysis("I hate you you")[0]
    assert sent["label"] == "NEGATIVE"
    assert sent["score"] > .9  

# basic transcription, don't specify a model if you care about the space in your .cache dir
def test_transcribe_mlk():
    transcriber = pipeline(task="automatic-speech-recognition")
    result = transcriber("https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/mlk.flac")["text"]
    assert "HAVE A DREAM" in result
    
def test_cat_recognition():
    vision_classifier = pipeline(model="google/vit-base-patch16-224")
    preds = vision_classifier(
        images="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
    )
    preds = [{"score": round(pred["score"], 4), "label": pred["label"]} for pred in preds]
    
    assert any('cat' in pred["label"] for pred in preds)
    
def test_zero_shot_class():
    classifier = pipeline(task="zero-shot-classification", model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")
    results = classifier(
        "I have a problem with my iphone that needs to be resolved asap!!",
        candidate_labels=["urgent", "not urgent", "phone", "tablet", "computer"],
    )
    assert results["labels"][0] == "urgent"
    assert results["scores"][0] > .4
    
# the function will return a bunch of nonsense that we can't assert but will verify that
# tensorflow probably works fine with transformer
def test_tf_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-cased")

    batch_sentences = [
        "But what about second breakfast?",
        "Don't think he knows about second breakfast, Pip.",
        "What about elevensies?",
    ]
    encoded_input = tokenizer(batch_sentences, padding=True, truncation=True, return_tensors="tf")
    assert str(type(encoded_input["input_ids"])) == "<class 'tensorflow.python.framework.ops.EagerTensor'>"
    
# the function will return a bunch of nonsense that we can't assert but will verify that
# pytorch probably works fine with transformer
def test_pytorch_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-cased")
    
    batch_sentences = [
    "But what about second breakfast?",
    "Don't think he knows about second breakfast, Pip.",
    "What about elevensies?",
    ]
    encoded_input = tokenizer(batch_sentences, padding=True, truncation=True, return_tensors="pt")
    print(encoded_input)

    assert str(type(encoded_input["input_ids"])) == "<class 'torch.Tensor'>"
    