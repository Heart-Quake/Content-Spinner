from __future__ import annotations

from template_engine import TemplateSyntaxError, find_unknown_variables, parse_template


def test_parse_template_rejects_unbalanced_braces() -> None:
    try:
        parse_template("{Bonjour|Salut", allow_variables=False)
    except TemplateSyntaxError as error:
        assert "n'est pas refermée" in str(error)
    else:
        raise AssertionError("Une accolade non refermée aurait dû être refusée.")


def test_parse_template_rejects_variables_in_simple_mode() -> None:
    try:
        parse_template("[Ville] est belle", allow_variables=False)
    except TemplateSyntaxError as error:
        assert "réservés aux variables du mode CSV" in str(error)
    else:
        raise AssertionError("Les variables ne devraient pas être autorisées en mode simple.")


def test_parse_template_collects_nested_variables_in_order() -> None:
    template = parse_template("[Ville] {historique|{très|vraiment} vivante} avec [Population]", allow_variables=True)
    assert template.variable_names == ("Ville", "Population")


def test_render_template_supports_nested_spins() -> None:
    template = parse_template("{Bonjour|Salut} {monde|tout le monde}", allow_variables=False)
    generated_text = template.render()
    assert generated_text in {
        "Bonjour monde",
        "Bonjour tout le monde",
        "Salut monde",
        "Salut tout le monde",
    }


def test_find_unknown_variables_returns_only_missing_names() -> None:
    template = parse_template("[Ville] en [Region]", allow_variables=True)
    assert find_unknown_variables(template, ["Ville"]) == ("Region",)
