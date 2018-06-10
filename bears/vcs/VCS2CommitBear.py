
import abc
import logging
import re
from contextlib import redirect_stdout

from giturlparse import parse

from coalib.bears.GlobalBear import GlobalBear
from coalib.results.HiddenResult import HiddenResult
from coalib.results.Result import Result
from coalib.settings.Setting import typed_list
from coalib.settings.FunctionMetadata import FunctionMetadata


class CommitResult(HiddenResult):
    def run(self):
        yield HiddenResult(self, commit_info)


class _VCSCommitBear(GlobalBear):
    __metaclass__ = abc.ABCMeta
    AUTHORS = {'The coala developers'}
    AUTHORS_EMAILS = {'coala-devel@googlegroups.com'}
    LICENSE = 'AGPL-3.0'
    CAN_DETECT = {'Formatting'}

    @abc.abstractmethod
    def get_head_commit(self):
        """
        Return the commit message from the head commit
        """

    def run(self):
        (stdout, stderr) = self.get_head_commit()

        if stderr:
            vcs_name = list(self.LANGUAGES)[0].lower()+':'
            self.err(vcs_name, repr(stderr))
            return

        commit_info = stdout
        yield CommitResult(self, (commit_info,), "HEAD commit information")