import pytest

from libraryhub.dsa.categories import (
    CategoryNode,
    build_category_tree,
    count_items,
    find_category,
    path_to,
    print_tree,
    total_items,
    total_items_iterative,
)
from libraryhub.errors import ValidationError

# One (category, parent category) pair per book of the starter catalogue.
STARTER = [
    ("Biography", ""),
    ("Fiction", ""),
    ("Software Engineering", "Technology"),
    ("Programming", "Technology"),
    ("History", ""),
    ("Reference", ""),
    ("Magazines", ""),
]

BRIEF_TREE = [
    "Library (7)",
    "  Biography (1)",
    "  Fiction (1)",
    "  History (1)",
    "  Magazines (1)",
    "  Reference (1)",
    "  Technology (2)",
    "    Programming (1)",
    "    Software Engineering (1)",
]


def printed(root):
    lines = []
    print_tree(root, lines.append)
    return lines


# --- The samples of the brief ---------------------------------------------------


def test_print_tree_matches_the_brief():
    assert printed(build_category_tree(STARTER)) == BRIEF_TREE


def test_count_items_matches_the_brief():
    assert count_items(build_category_tree(STARTER), "Technology") == 2


def test_path_to_matches_the_brief():
    root = build_category_tree(STARTER)
    assert path_to(root, "Software Engineering") == [
        "Library",
        "Technology",
        "Software Engineering",
    ]
    assert path_to(root, "Cooking") is None


def test_the_starter_catalogue_of_the_library_gives_the_same_tree(library_world):
    root = library_world.library.category_tree()
    assert printed(root) == BRIEF_TREE


# --- Counting and finding -----------------------------------------------------------


def test_count_items_for_the_root_a_leaf_and_an_unknown_category():
    root = build_category_tree(STARTER)
    assert count_items(root, "Library") == 7
    assert count_items(root, "Programming") == 1
    assert count_items(root, "Cooking") is None


def test_find_category_returns_the_node_or_none():
    root = build_category_tree(STARTER)
    node = find_category(root, "Technology")
    assert node is not None
    assert [child.name for child in node.children] == [
        "Programming",
        "Software Engineering",
    ]
    assert find_category(root, "Cooking") is None


def test_path_to_the_root_is_just_the_root():
    assert path_to(build_category_tree(STARTER), "Library") == ["Library"]


# --- Building ---------------------------------------------------------------------------


def test_an_empty_catalogue_gives_a_root_with_no_items():
    assert printed(build_category_tree([])) == ["Library (0)"]


def test_several_items_in_one_category_are_all_counted():
    root = build_category_tree([("Fiction", ""), ("Fiction", None), ("Fiction", "")])
    assert printed(root) == ["Library (3)", "  Fiction (3)"]


def test_an_item_without_a_category_is_left_out():
    root = build_category_tree([("", ""), ("Fiction", "")])
    assert total_items(root) == 1


def test_children_are_sorted_by_name_whatever_the_order_in_the_data():
    root = build_category_tree([("Zoology", ""), ("Art", ""), ("Music", "")])
    assert [child.name for child in root.children] == ["Art", "Music", "Zoology"]


def test_three_levels_deep():
    root = build_category_tree(
        [("Python", "Programming"), ("Programming", "Technology"), ("Algorithms", "Programming")]
    )
    assert path_to(root, "Python") == ["Library", "Technology", "Programming", "Python"]
    assert count_items(root, "Technology") == 3
    assert count_items(root, "Programming") == 3


def test_a_category_with_two_parents_is_refused():
    with pytest.raises(ValidationError, match="two different parents"):
        build_category_tree([("Python", "Technology"), ("Python", "Science")])


@pytest.mark.parametrize(
    "pairs",
    [
        [("A", "B"), ("B", "A")],  # a loop of two
        [("A", "A")],  # a category that is its own parent
    ],
)
def test_a_loop_of_parents_is_refused(pairs):
    with pytest.raises(ValidationError, match="loop"):
        build_category_tree(pairs)


# --- Recursive and iterative counting ----------------------------------------------------


def make_chain(depth):
    """A tree with one child per level and one item in every node but the top."""
    top = CategoryNode("level 0")
    node = top
    for level in range(1, depth):
        child = CategoryNode(f"level {level}", own_items=1)
        node.children.append(child)
        node = child
    return top


def test_both_ways_of_counting_agree():
    root = build_category_tree(STARTER)
    assert total_items(root) == total_items_iterative(root) == 7


def test_a_very_deep_tree_breaks_the_recursive_count_but_not_the_iterative_one():
    deep = make_chain(5_000)
    assert total_items_iterative(deep) == 4_999
    with pytest.raises(RecursionError):
        total_items(deep)