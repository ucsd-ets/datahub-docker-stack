def test_litellm_imports():
    import litellm

    assert hasattr(litellm, "completion")
    assert hasattr(litellm, "acompletion")


def test_openai_sdk_imports():
    import openai

    assert hasattr(openai, "OpenAI")
