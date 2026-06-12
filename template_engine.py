from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Mapping, Union


class TemplateSyntaxError(ValueError):
    """Erreur de syntaxe remontée au moment de l’analyse du template."""


class UnknownVariableError(ValueError):
    """Erreur remontée lorsqu’une variable demandée est absente du contexte."""


@dataclass(frozen=True)
class TextNode:
    """Segment brut du template."""

    value: str


@dataclass(frozen=True)
class VariableNode:
    """Référence vers une colonne CSV."""

    name: str


@dataclass(frozen=True)
class SpinNode:
    """Bloc de spin contenant plusieurs options possibles."""

    options: tuple[tuple["TemplateNode", ...], ...]


TemplateNode = Union[TextNode, VariableNode, SpinNode]
DEFAULT_RANDOM = Random()


@dataclass(frozen=True)
class TemplateDefinition:
    """Template pré-analysé prêt à être rendu plusieurs fois rapidement."""

    nodes: tuple[TemplateNode, ...]
    variable_names: tuple[str, ...]

    def render(self, variables: Mapping[str, str] | None = None, rng: Random | None = None) -> str:
        """Génère une variation à partir du template compilé."""
        active_variables = variables or {}
        active_rng = rng or DEFAULT_RANDOM
        return _render_sequence(self.nodes, active_variables, active_rng)


def parse_template(template_text: str, *, allow_variables: bool) -> TemplateDefinition:
    """Compile le template en arbre de nœuds pour sécuriser la génération."""
    if not template_text or not template_text.strip():
        raise TemplateSyntaxError("Le template est vide.")

    parser = TemplateParser(template_text, allow_variables=allow_variables)
    nodes = parser.parse()
    variable_names = collect_variable_names(nodes)
    return TemplateDefinition(nodes=nodes, variable_names=variable_names)


def find_unknown_variables(template: TemplateDefinition, available_columns: list[str]) -> tuple[str, ...]:
    """Liste les variables utilisées mais absentes des colonnes autorisées."""
    available_set = {column.strip() for column in available_columns}
    return tuple(name for name in template.variable_names if name not in available_set)


class TemplateParser:
    """Petit parseur récursif adapté aux spins imbriqués."""

    def __init__(self, template_text: str, *, allow_variables: bool):
        self.template_text = template_text
        self.allow_variables = allow_variables
        self.length = len(template_text)

    def parse(self) -> tuple[TemplateNode, ...]:
        """Analyse le texte complet."""
        nodes, index = self._parse_sequence(0, stop_chars=set())
        if index != self.length:
            raise TemplateSyntaxError("Le template contient des caractères inattendus.")
        return nodes

    def _parse_sequence(self, index: int, stop_chars: set[str]) -> tuple[tuple[TemplateNode, ...], int]:
        """Parse une séquence jusqu’à un séparateur de haut niveau."""
        nodes: list[TemplateNode] = []
        buffer: list[str] = []

        while index < self.length:
            current_char = self.template_text[index]

            if current_char in stop_chars:
                break

            if current_char == "{":
                flush_text_buffer(buffer, nodes)
                spin_node, index = self._parse_spin(index + 1)
                nodes.append(spin_node)
                continue

            if current_char == "[":
                if not self.allow_variables:
                    raise TemplateSyntaxError("Les crochets [] sont réservés aux variables du mode CSV.")

                flush_text_buffer(buffer, nodes)
                variable_node, index = self._parse_variable(index + 1)
                nodes.append(variable_node)
                continue

            if current_char == "}":
                raise TemplateSyntaxError("Accolade fermante '}' sans accolade ouvrante correspondante.")

            if current_char == "]":
                raise TemplateSyntaxError("Crochet fermant ']' sans crochet ouvrant correspondant.")

            buffer.append(current_char)
            index += 1

        flush_text_buffer(buffer, nodes)
        return tuple(nodes), index

    def _parse_spin(self, index: int) -> tuple[SpinNode, int]:
        """Parse un bloc de spin délimité par des accolades."""
        options: list[tuple[TemplateNode, ...]] = []

        while True:
            option_nodes, index = self._parse_sequence(index, stop_chars={"|", "}"})

            if not sequence_has_visible_content(option_nodes):
                raise TemplateSyntaxError("Chaque spin doit contenir des options non vides.")

            if index >= self.length:
                raise TemplateSyntaxError("Une accolade ouvrante '{' n'est pas refermée.")

            delimiter = self.template_text[index]
            options.append(option_nodes)
            index += 1

            if delimiter == "}":
                break

        if len(options) < 2:
            raise TemplateSyntaxError("Un spin doit contenir au moins deux options.")

        return SpinNode(options=tuple(options)), index

    def _parse_variable(self, index: int) -> tuple[VariableNode, int]:
        """Parse une variable CSV référencée entre crochets."""
        variable_start = index

        while index < self.length and self.template_text[index] != "]":
            current_char = self.template_text[index]
            if current_char in "{}[]|":
                raise TemplateSyntaxError("Le nom d’une variable ne peut pas contenir de délimiteur de spin.")
            index += 1

        if index >= self.length:
            raise TemplateSyntaxError("Un crochet ouvrant '[' n'est pas refermé.")

        variable_name = self.template_text[variable_start:index].strip()
        if not variable_name:
            raise TemplateSyntaxError("Le nom d’une variable ne peut pas être vide.")

        return VariableNode(name=variable_name), index + 1


def flush_text_buffer(buffer: list[str], nodes: list[TemplateNode]) -> None:
    """Consolide les segments de texte pour alléger l’arbre final."""
    if buffer:
        nodes.append(TextNode("".join(buffer)))
        buffer.clear()


def sequence_has_visible_content(nodes: tuple[TemplateNode, ...]) -> bool:
    """Empêche les options vides ou composées uniquement d’espaces."""
    for node in nodes:
        if isinstance(node, TextNode) and node.value.strip():
            return True
        if isinstance(node, (VariableNode, SpinNode)):
            return True
    return False


def collect_variable_names(nodes: tuple[TemplateNode, ...]) -> tuple[str, ...]:
    """Collecte les variables en conservant leur ordre d’apparition."""
    ordered_names: list[str] = []
    seen_names: set[str] = set()

    def visit(sequence: tuple[TemplateNode, ...]) -> None:
        for node in sequence:
            if isinstance(node, VariableNode):
                if node.name not in seen_names:
                    ordered_names.append(node.name)
                    seen_names.add(node.name)
            elif isinstance(node, SpinNode):
                for option in node.options:
                    visit(option)

    visit(nodes)
    return tuple(ordered_names)


def _render_sequence(nodes: tuple[TemplateNode, ...], variables: Mapping[str, str], rng: Random) -> str:
    """Rend récursivement une séquence de nœuds."""
    rendered_parts: list[str] = []

    for node in nodes:
        if isinstance(node, TextNode):
            rendered_parts.append(node.value)
        elif isinstance(node, VariableNode):
            if node.name not in variables:
                raise UnknownVariableError(f"Variable absente du contexte : [{node.name}]")
            rendered_parts.append(str(variables[node.name]))
        else:
            selected_option = rng.choice(node.options)
            rendered_parts.append(_render_sequence(selected_option, variables, rng))

    return "".join(rendered_parts)
