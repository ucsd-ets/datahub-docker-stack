from scripts.v2.tree import Node


class DockerDriver:
    def build_image(self, node: Node):
        """Build a docker image from a node

        Args:
            node (Node): node to build
        """
        pass


    def push_image(self, node: Node) -> bool:
        """push image to dockerhub

        Args:
            node (Node): image to push

        Returns:
            bool: true if successfully pushed to dockerhub
        """
        pass

    def clear_cache(self):
        pass

def build_and_test_tree(self, root: Node, docker_driver: DockerDriver):
    # Run BFS or whatever search method
    # goal: make sure that the code can continue if a leaf node fails
    q = [root]
    while q:
        for _ in range(len(q)):
            pass
            # TODO
            # if marked for rebuild
            #   build
            #   test
            #   push
            #   integration tests
            #   update wiki
        
    pass