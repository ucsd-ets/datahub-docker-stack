# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from plumbum.cmd import git


class GitHelper:
    @staticmethod
    def commit_hash() -> str:
        return git["rev-parse", "HEAD"]().strip()

    @staticmethod
    def commit_hash_tag() -> str:
        return GitHelper.commit_hash()[:7]

    @staticmethod
    def commit_message() -> str:
        return git["log", -1, "--pretty=%B"]().strip()

    @staticmethod
    def commit_changed_files() -> list:
        return git['log', -1, '--name-only', '--pretty=format:']().split()


if __name__ == "__main__":
    print("Git hash:", GitHelper.commit_hash())
    print("Git hash shortened:", GitHelper.commit_hash_tag())
    print("Git message:", GitHelper.commit_message())
    print("Git changed files:", GitHelper.commit_changed_files())