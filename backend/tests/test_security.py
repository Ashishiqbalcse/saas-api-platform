from app.auth.security import generate_api_key, get_key_prefix, hash_api_key, verify_api_key


def test_api_key_is_prefixed_and_verifiable():
    raw = generate_api_key()
    hashed = hash_api_key(raw)

    assert raw.startswith("sk_live_")
    assert get_key_prefix(raw).startswith("sk_live_")
    assert hashed != raw
    assert verify_api_key(raw, hashed)
    assert not verify_api_key(raw + "x", hashed)
