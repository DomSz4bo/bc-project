
def extract_block(block: str, language_tag: str = ""):
    return block.strip("`").removeprefix(language_tag).removeprefix("\n")