from claimflow.generator import generate_events


def test_generator_is_deterministic_and_referentially_consistent() -> None:
    events = list(generate_events(250, seed=7))
    repeat = list(generate_events(250, seed=7))

    assert len(events) == 250
    assert [event.event_id for event in events] == [event.event_id for event in repeat]
    assert len({event.event_id for event in events}) == 250

    policy_ids = {
        event.payload["policy_id"] for event in events if event.event_type.startswith("policy.")
    }
    claim_events = [event for event in events if event.event_type.startswith("claim.")]
    assert claim_events
    assert all(event.payload["policy_id"] in policy_ids for event in claim_events)


def test_generator_rejects_too_small_dataset() -> None:
    try:
        list(generate_events(5))
    except ValueError as exc:
        assert "at least 20" in str(exc)
    else:
        raise AssertionError("small dataset should have been rejected")
