from app.auth.security import generate_api_key, get_key_prefix, hash_api_key

raw_key = generate_api_key()

print("RAW KEY :", raw_key)
print("PREFIX  :", get_key_prefix(raw_key))
print("HASH    :", hash_api_key(raw_key))