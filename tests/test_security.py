from claimflow.security import deterministic_token, protect_pii


def test_tokens_are_stable_but_do_not_expose_source() -> None:
    first = deterministic_token("Person@Example.com", key=b"test-key")
    second = deterministic_token(" person@example.com ", key=b"test-key")

    assert first == second
    assert "person" not in first
    assert first.startswith("tok_")


def test_protect_pii_replaces_sensitive_fields() -> None:
    protected = protect_pii(
        {"claim_id": "clm-1", "claimant_name": "Jamie Doe", "claimant_email": "j@example.com"}
    )

    assert protected["claim_id"] == "clm-1"
    assert "claimant_name" not in protected
    assert "claimant_email" not in protected
    assert protected["claimant_name_token"].startswith("tok_")
