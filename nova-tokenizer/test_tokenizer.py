from tokenizer import NovaTokenizer

def test_round_trip():
    tok = NovaTokenizer.default()
    for sample in ["", "hello", "Nova AI", "Héllo — 世界 🌍", "line 1\nline 2\t✓"]:
        assert tok.decode(tok.encode(sample)) == sample

def test_special_tokens():
    tok = NovaTokenizer.default()
    ids = tok.encode("Nova", add_bos=True, add_eos=True)
    assert ids[0] == tok.special_tokens["<bos>"]
    assert ids[-1] == tok.special_tokens["<eos>"]
    assert tok.decode(ids) == "Nova"

if __name__ == "__main__":
    test_round_trip()
    test_special_tokens()
    print("NOVA_TOKENIZER_TESTS_PASS")
