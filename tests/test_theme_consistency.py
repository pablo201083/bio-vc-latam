"""Guards against the class of bug where a theme dict/adjacency uses a name
that isn't in the sealed BIO_THEMES taxonomy (e.g. the "Fermentation Economy"
incident where a stale theme name leaked into scoring code)."""
from src.vocabularies import BIO_THEMES, BIO_THEME_ALIASES
from src.intelligence import BIO_THEME_ADJACENCY, _ORG_FOCUS_THEME_KEYWORDS, _theme_overlap
from src.intro_builder import _THEME_ORG_KEYWORDS, _CORP_THEME_KEYWORDS

VALID_THEMES = set(BIO_THEMES) | set(BIO_THEME_ALIASES)


def test_adjacency_keys_are_valid_themes():
    for a, b in BIO_THEME_ADJACENCY:
        assert a in VALID_THEMES, f"{a!r} not in BIO_THEMES/aliases"
        assert b in VALID_THEMES, f"{b!r} not in BIO_THEMES/aliases"


def test_intelligence_keyword_dict_keys_are_valid_themes():
    for theme in _ORG_FOCUS_THEME_KEYWORDS:
        assert theme in VALID_THEMES, f"{theme!r} not in BIO_THEMES/aliases"


def test_intro_builder_keyword_dict_keys_are_valid_themes():
    for theme in _THEME_ORG_KEYWORDS:
        assert theme in VALID_THEMES, f"{theme!r} not in BIO_THEMES/aliases"
    for theme in _CORP_THEME_KEYWORDS:
        assert theme in VALID_THEMES, f"{theme!r} not in BIO_THEMES/aliases"


def test_theme_overlap_known_pair():
    assert _theme_overlap(
        "Biomanufacturing & Platform Technologies", "Food Systems & Alt Proteins"
    ) == 0.45


def test_theme_overlap_identity_and_unknown():
    assert _theme_overlap("Therapeutics", "Therapeutics") == 1.0
    assert _theme_overlap("Therapeutics", "") == 0.0
    assert _theme_overlap("", "") == 0.0
