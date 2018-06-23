import abc

from bears.vcs.git.GitCommitMetadataBear import COMMIT_TYPE
from coalib.bears.GlobalBear import GlobalBear
from coalib.results.HiddenResult import HiddenResult
from coala_utils.decorators import (enforce_signature, generate_ordering,
                                    generate_repr)


@generate_repr(('id', hex),
               'origin',
               'raw_commit_message',
               'commit_sha',
               'parent_commits',
               'commit_type',
               'modified_files',
               'added_files',
               'deleted_files')
@generate_ordering('raw_commit_message',
                   'commit_sha',
                   'parent_commits',
                   'commit_type',
                   'modified_files',
                   'added_files',
                   'deleted_files',
                   'severity',
                   'confidence',
                   'origin',
                   'message_base',
                   'message_arguments',
                   'aspect',
                   'additional_info',
                   'debug_msg')
class CommitResult(HiddenResult):

    @enforce_signature
    def __init__(self, origin,
                 raw_commit_message: str,
                 commit_sha: str,
                 parent_commits: list,
                 commit_type: COMMIT_TYPE,
                 modified_files: list,
                 added_files: list,
                 deleted_files: list):

        super().__init__(origin, '')
        self.raw_commit_message = raw_commit_message
        self.commit_sha = commit_sha
        self.parent_commits = parent_commits
        self.commit_type = commit_type
        self.modified_files = modified_files
        self.added_files = added_files
        self.deleted_files = deleted_files


class VCSCommitMetadataBear(GlobalBear):
    __metaclass__ = abc.ABCMeta
    AUTHORS = {'The coala developers'}
    AUTHORS_EMAILS = {'coala-devel@googlegroups.com'}
    LICENSE = 'AGPL-3.0'

    @abc.abstractmethod
    def get_head_commit(self):
        """
        Return the commit message from the head commit.
        """

    @abc.abstractmethod
    def analyze_git_commit(self, head_commit):
        """
        Check the current commit at HEAD.

        Return the commit information such as commit message,
        type of commit, commit SHA, modified, added and
        delete files by the commit.

        :param head_commit: The commit message at HEAD.
        :return:            A tuple comprising of commit message,
                            commit sha, list of parent commits,
                            type of commit viz. simple or merge
                            commit and lists of modified,
                            added and deleted files.
        """

    def run(self, **kwargs):
        """
        This bear returns information about the HEAD commit
        as HiddenResult which can be used for inspection by
        other bears.
        """
        head_commit, error = self.get_head_commit()

        if error:
            vcs_name = list(self.LANGUAGES)[0].lower()+':'
            self.err(vcs_name, repr(error))
            return

        for (raw_commit_message, commit_sha, parent_commits,
             commit_type, modified_files, added_files,
             deleted_files) in self.analyze_commit(
                head_commit):

            yield CommitResult(self, raw_commit_message, commit_sha,
                               parent_commits, commit_type, modified_files,
                               added_files, deleted_files)
