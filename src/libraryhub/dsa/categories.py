"""The category tree and its recursive functions.

Two things live here. `PARENT_CATEGORY` and `top_category` (used by the
catalogue sort) say which category belongs under which. The rest turns those
parents into a tree (Library -> Technology -> Programming) and walks it
recursively, because a tree is made of smaller trees: a category's answer is
built from the answers of its children. One walk, `total_items`, also has an
iterative twin that does not use the call stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from libraryhub.errors import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

ROOT_NAME = "Library"
INDENT = "  "

# Child category -> parent category. Anything not listed is its own top level.
PARENT_CATEGORY = {
    "Programming": "Technology",
    "Software Engineering": "Technology",
}


def top_category(category: str) -> str:
    """The top-level category: Programming and Software Engineering are Technology."""
    return PARENT_CATEGORY.get(category, category)


@dataclass(eq=False, repr=False)
class CategoryNode:
    """One category: the items filed directly in it and the categories below it."""

    name: str
    own_items: int = 0
    children: list[CategoryNode] = field(default_factory=list)


# --- Counting ---------------------------------------------------------------


def total_items(node: CategoryNode) -> int:
    """Items in this category and everything below it.

    Base case: a node with no children is just its own items.
    Smaller problem: the same question for each child.
    """
    return node.own_items + sum(total_items(child) for child in node.children)


def total_items_iterative(node: CategoryNode) -> int:
    """The same answer with a list used as a stack, so depth does not matter.

    Python allows about 1,000 nested calls. A tree 10,000 levels deep makes the
    recursive version raise RecursionError. This one only needs memory.
    """
    total = 0
    pending = [node]
    while pending:
        current = pending.pop()
        total += current.own_items
        pending.extend(current.children)
    return total


# --- Finding ------------------------------------------------------------------


def find_category(node: CategoryNode, name: str) -> CategoryNode | None:
    """The node called `name` in this tree, or None.

    Base case: this node has the name, or it has no children left to try.
    Smaller problem: search each child's tree.
    """
    if node.name == name:
        return node
    for child in node.children:
        found = find_category(child, name)
        if found is not None:
            return found
    return None


def count_items(root: CategoryNode, name: str) -> int | None:
    """Items under the category `name`, or None when there is no such category."""
    node = find_category(root, name)
    return None if node is None else total_items(node)


def path_to(node: CategoryNode, name: str) -> list[str] | None:
    """Names from this node down to `name`, or None when it is not below here.

    Base case: this node is the one, so the path is just its name.
    Smaller problem: ask each child for its path, and put this name in front.
    """
    if node.name == name:
        return [node.name]
    for child in node.children:
        path = path_to(child, name)
        if path is not None:
            return [node.name, *path]
    return None


# --- Printing -------------------------------------------------------------------


def tree_lines(node: CategoryNode, depth: int = 0) -> list[str]:
    """'Technology (2)' lines, each child indented two spaces more than its parent."""
    lines = [f"{INDENT * depth}{node.name} ({total_items(node)})"]
    for child in node.children:
        lines.extend(tree_lines(child, depth + 1))
    return lines


def print_tree(root: CategoryNode, output: Callable[[str], None] = print) -> None:
    """Send the tree to `output` one line at a time."""
    for line in tree_lines(root):
        output(line)


# --- Building ---------------------------------------------------------------------


def build_category_tree(pairs: Iterable[tuple[str, str | None]]) -> CategoryNode:
    """Make the tree from one (category, parent category) pair per item.

    A blank parent means the category sits directly under the root. An item
    with a blank category is left out. Category names must be unique, and each
    category can have only one parent. Children are sorted by name.
    """
    root = CategoryNode(ROOT_NAME)
    nodes: dict[str, CategoryNode] = {}
    parent_of: dict[str, str] = {}
    filed = 0
    for category, parent in pairs:
        if not category:
            continue
        nodes.setdefault(category, CategoryNode(category)).own_items += 1
        filed += 1
        if parent:
            nodes.setdefault(parent, CategoryNode(parent))
            if parent_of.setdefault(category, parent) != parent:
                raise ValidationError(
                    "category",
                    f"Category '{category}' has two different parents: "
                    f"'{parent_of[category]}' and '{parent}'.",
                )
    for name, parent in parent_of.items():
        nodes[parent].children.append(nodes[name])
    for name, node in nodes.items():
        if name not in parent_of:
            root.children.append(node)  # no parent: it hangs under the root
    for node in (root, *nodes.values()):
        node.children.sort(key=lambda child: child.name)
    if total_items_iterative(root) != filed:  # a loop of parents is unreachable
        raise ValidationError("category", "The category parents form a loop.")
    return root


def build_tree_from_categories(categories: Iterable[str]) -> CategoryNode:
    """Make the tree from one category name per item, using PARENT_CATEGORY."""
    return build_category_tree(
        (category, PARENT_CATEGORY.get(category)) for category in categories
    )