import yaml
from collections import deque


class DockerImageDef:
    def __init__(self, name, img_name, depend_on=None) -> None:
        self.name = name
        self.img_name = img_name
        self.depend_on = depend_on
        self.to_build = False
        self.downstream = []
        self.dbuildenv = {}
        self.skip_plans = []

    def __repr__(self) -> str:
        return f'DockerImageDef({self.name})'

    def subtree_order(self):
        """pre-order DFS"""
        stack = deque()
        stack.append(self)
        order = []
        while stack:
            curr = stack.pop()
            order.append(curr)
            for child in curr.downstream:
                stack.append(child)
        return order

    def get_level_order(self):
        '''BFS'''
        queue = [self]
        order = {}
        cnt = 0
        while queue:
            curr = queue.pop(0)
            for child in curr.downstream:
                queue.append(child)
            order[curr] = cnt
            cnt += 1
        return order
