"""Initial processing of the shell output from the yum repolist data."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessEnableYumRepolist(process.Processor):
    """Process the list of enabled yum repositories."""

    KEY = "yum_enabled_repolist"
    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        repos = []
        out_lines = output["stdout_lines"]
        found_repos = False
        for line in out_lines:
            if "repo id" in line:
                out_lines = out_lines[out_lines.index(line) + 1 :]
                found_repos = True
        if found_repos:
            for line in out_lines:
                repo, _, remainder = line.partition(" ")
                repo_name, _, _ = remainder.rpartition(" ")
                repo = repo.strip()
                repo_name = repo_name.strip()
                if repo and repo_name:
                    repos.append({"name": repo_name, "repo": repo})

        return repos
