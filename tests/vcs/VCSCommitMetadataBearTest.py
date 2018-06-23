import unittest
import unittest.mock

from bears.vcs.git.GitCommitMetadataBear import COMMIT_TYPE
from bears.vcs.VCSCommitMetadataBear import (VCSCommitMetadataBear,
    CommitResult)


class CommitResultTest(unittest.TestCase):
    def setUp(self):
        self.raw_commit_message = 'raw_commit_message'
        self.commit_sha = 'commit_sha'
        self.parent_commits = ['parent_commits']
        self.modified_files = ['modified_files']
        self.added_files = ['added_files']
        self.deleted_files = ['deleted_files']

    def test_repr(self):
        repr_result = repr(CommitResult(VCSCommitBear,
                                        self.raw_commit_message,
                                        self.commit_sha,
                                        self.parent_commits,
                                        COMMIT_TYPE.simple_commit,
                                        self.modified_files,
                                        self.added_files,
                                        self.deleted_files,))

        repr_regex = (
            r'<CommitResult object\(id=.+, origin=\'bearclass\', '
            r'raw_commit_message=\'.+\', '
            r'commit_sha=\'.+\', '
            r'parent_commits=\[.+\], '
            r'commit_type=<COMMIT_TYPE.simple_commit: 0>, '
            r'modified_files=\[.+\], '
            r'added_files=\[.+\], '
            r'deleted_files=\[.+\]\) at .+>'
            )
        self.assertRegex(repr_result, repr_regex)
