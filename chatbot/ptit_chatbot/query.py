"""Vietnamese PTIT query cleanup and abbreviation expansion."""

import re


ABBREVIATIONS = {
    "ptxt": "phương thức xét tuyển",
    "đgnl": "đánh giá năng lực",
    "dgnl": "đánh giá năng lực",
    "cntt": "công nghệ thông tin",
    "attt": "an toàn thông tin",
    "cnđpt": "công nghệ đa phương tiện",
    "đpt": "đa phương tiện",
    "ktx": "ký túc xá",
    "hphi": "học phí",
    "hp": "học phí",
    "hb": "học bổng",
    "ts": "tuyển sinh",
    "xt": "xét tuyển",
    "đh": "đại học",
    "dh": "đại học",
    "sv": "sinh viên",
    "hv": "học viện",
    "t" : "tôi",
    "m" : "mày",
    "b" : "bạn",
    "bn" : "bạn",
}

_ABBREVIATION_PATTERN = re.compile(
    r"(?<!\w)(" + "|".join(map(re.escape, sorted(ABBREVIATIONS, key=len, reverse=True))) + r")(?!\w)",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")


def expand_query(question: str) -> str:
    """Expand known PTIT shorthand without changing the user's original text."""
    normalized = _WHITESPACE.sub(" ", question).strip()
    return _ABBREVIATION_PATTERN.sub(
        lambda match: ABBREVIATIONS[match.group(0).lower()], normalized
    )


def search_terms(question: str, limit: int = 8) -> str:
    """Create a compact search phrase from an expanded conversational question."""
    expanded = expand_query(question).lower()
    expanded = re.sub(r"[^\w\s-]", " ", expanded, flags=re.UNICODE)
    words = _WHITESPACE.split(expanded)
    stop_words = {
        "cho", "mình", "tôi", "em", "anh", "chị", "với", "về", "của", "là",
        "có", "những", "các", "nào", "bao", "nhiêu", "thế", "năm", "nay",
        "giúp", "xin", "hỏi", "muốn", "biết", "ptit",
    }
    useful = [word for word in words if word not in stop_words]
    return " ".join(useful[:limit] or words[:limit])
