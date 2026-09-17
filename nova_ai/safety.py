import re

BLOCK_PATTERNS=[
    r'\b(?:build|make|create)\s+(?:a\s+)?bomb\b',
    r'\b(?:malware|ransomware|keylogger)\b',
    r'\b(?:steal|dump)\s+passwords?\b',
    r'\b(?:buy|sell)\s+(?:illegal drugs|heroin|cocaine)\b',
]

def moderate(text:str)->tuple[bool,str]:
    t=text.lower()
    for p in BLOCK_PATTERNS:
        if re.search(p,t):
            return False,'I can’t help with harmful or illegal instructions.'
    return True,''
