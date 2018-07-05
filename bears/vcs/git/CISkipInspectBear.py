import re

from bears.vcs.git.GitCommitBear import GitCommitBear
from coalib.bears.GlobalBear import GlobalBear
from coalib.results.Result import Result


class CISkipInspectBear(GlobalBear):
    LANGUAGES = {'Git'}
    AUTHORS = {'The coala developers'}
    AUTHORS_EMAILS = {'coala-devel@googlegroups.com'}
    LICENSE = 'AGPL-3.0'

    CI_PROVIDERS_METADATA = {
          'Circle CI': r'\[ci skip\]|\[skip ci\]',
          'Travis CI': r'\[ci skip\]|\[skip ci\]',
          'Appveyor CI': r'\[skip ci\]|\[ci skip\]|\[skip appveyor\]',
          }

    BEAR_DEPS = {GitCommitBear}

    def run(self, dependency_results,
            ci_engines_used: list = [],
            allow_ciskip_commit: bool = True,
            **kwargs):
        """
        Inspect the HEAD commit to check if it disables
        CI build.

        :param allow_ciskip_commit: whether disaling CI
                                    build is allowed or
                                    not.
        :param ci_engines_used:     CI engines used in
                                    the project.
        """
        for result in dependency_results[GitCommitBear.name]:

            if not allow_ciskip_commit:
                yield Result(self, 'Skipping CI build is not allowed.')
                return

            for ci_engine in ci_engines_used:

                if ci_engine in self.CI_PROVIDERS_METADATA:
                    supported_regex = self.CI_PROVIDERS_METADATA[ci_engine]

                    if ci_engine == 'Appveyor CI':
                        pos = result.raw_commit_message.find('\n')
                        commit_title = result.raw_commit_message[:pos] if (
                            pos != -1) else result.raw_commit_message

                        match = re.search(supported_regex, commit_title)

                    else:
                        match = re.search(
                            supported_regex, result.raw_commit_message)

                    if match:

                        all_files = (result.modified_files +
                                     result.added_files + result.deleted_files)

                        for file in all_files:
                            if (file.endswith('Test.py') or
                                    file.endswith('coafile')):
                                yield Result(
                                    self,
                                    'This commit modifies test files or '
                                    'coafile files and cannot disable '
                                    'CI build.')
                                return
