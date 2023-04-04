from scripts.v2.tree import *

def test_load_spec():
    # TODO load fake yaml
    # compare
    pass


def test_build_tree():
    fake_spec = {
        'images': [
            
        ]
    }

    should_be = Node('root', '', [
        Node('child1', '', [], {}),
        Node('child2', '', [], {}),
        Node('child3', '', [], {}),
        Node('child4', '', [], {}),
    ], {})

    got = build_tree(fake_spec)

    assert got == should_be

def test_mark_rebuild():
    test_case = Node('root', '', [
        Node('child1', '', [], {}),
        Node('child2', '', [], {}),
        Node('child3', '', [], {}),
        Node('child4', '', [], {}),
    ], {}, rebuild=True)

    should_be = Node('root', '', [
        Node('child1', '', [], {}, rebuild=True),
        Node('child2', '', [], {},  rebuild=True),
        Node('child3', '', [], {}, rebuild=True),
        Node('child4', '', [], {}, rebuild=True)
    ], {}, rebuild=True)

    mark_rebuild(test_case)

    assert test_case == should_be