from scripts.tree import *
import pytest
import yaml

yamlPath = "tests/fake_spec.yml"
yamlDict = load_spec(yamlPath)

def test_load_spec():
    expect_images = {
        'root': {'image_name': 'ucsdets/root'}, 
        'child1': {'image_name': 'ucsdets/child1', 'depend_on': 'root'}, 
        'child2': {'image_name': 'ucsdets/child1', 'depend_on': 'root'}, 
        'child3': {'image_name': 'ucsdets/child3', 'depend_on': 'root'}, 
        'child4': {'image_name': 'ucsdets/child4', 'depend_on': 'root'}
    }
    
    assert yamlDict["images"] == expect_images


def test_build_tree():
    should_be = Node('ucsdets/root', 'gitnull', [
        Node('ucsdets/child1', 'gitnull', [], {}, filepath="images/child1"),
        Node('ucsdets/child2', 'gitnull', [], {}, filepath="images/child2"),
        Node('ucsdets/child3', 'gitnull', [], {}, filepath="images/child3"),
        Node('ucsdets/child4', 'gitnull', [], {}, filepath="images/child4"),
    ], {}, filepath="images/root")

    got = build_tree(yamlDict, [])

    got.print_info()
    should_be.print_info()
    assert got == should_be


def test_mark_rebuild_TopDown():
    should_be = Node('ucsdets/root', 'gitnull', [
        Node('ucsdets/child1', 'gitnull', [], {}, filepath="images/child1", rebuild=True),
        Node('ucsdets/child2', 'gitnull', [], {}, filepath="images/child2", rebuild=True),
        Node('ucsdets/child3', 'gitnull', [], {}, filepath="images/child3", rebuild=True),
        Node('ucsdets/child4', 'gitnull', [], {}, filepath="images/child4", rebuild=True),
    ], {}, filepath="images/root", rebuild=True)

    got = build_tree(yamlDict, ['root'])

    got.print_info()
    should_be.print_info()
    assert got == should_be

def test_mark_rebuild_BottomUp():
    should_be = Node('ucsdets/root', 'gitnull', [
        Node('ucsdets/child1', 'gitnull', [], {}, filepath="images/child1", rebuild=False),
        Node('ucsdets/child2', 'gitnull', [], {}, filepath="images/child2", rebuild=False),
        Node('ucsdets/child3', 'gitnull', [], {}, filepath="images/child3", rebuild=True),
        Node('ucsdets/child4', 'gitnull', [], {}, filepath="images/child4", rebuild=False),
    ], {}, filepath="images/root", rebuild=False)

    # NOTE: currently we use git commit short hash as image tag (which works like identifier) in Dockerhub
    # Thus, child3 rebuild should also mark rebuild on root. But this is handled in later (in runner.py)
    # In the future we plan to use branch name as tag and get rid off this issue.
    # But anyway, root.rebuild should be False here.

    got = build_tree(yamlDict, ['child3'])

    got.print_info()
    should_be.print_info()
    assert got == should_be

