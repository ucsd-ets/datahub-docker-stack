def test_litellm_imports():
    import litellm

    assert hasattr(litellm, "completion")
    assert hasattr(litellm, "acompletion")


def test_openai_sdk_imports():
    import openai

    assert hasattr(openai, "OpenAI")


def test_litellm_sees_openai_key_in_environment(monkeypatch):
    # validate_environment only inspects env vars -- it makes no network call.
    import litellm

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    result = litellm.utils.validate_environment("gpt-4o-mini")

    assert result["keys_in_environment"] is True
    assert result["missing_keys"] == []


def test_litellm_reports_missing_openai_key(monkeypatch):
    import litellm

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = litellm.utils.validate_environment("gpt-4o-mini")

    assert result["keys_in_environment"] is False
    assert "OPENAI_API_KEY" in result["missing_keys"]


def test_openai_client_reads_env_credentials(monkeypatch):
    import openai

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://litellm.example.ucsd.edu/v1")

    client = openai.OpenAI()

    assert client.api_key == "sk-test-not-a-real-key"
    assert str(client.base_url).rstrip("/") == "https://litellm.example.ucsd.edu/v1"
