import shutil
import unittest
import unittest.mock
from queue import Queue

from bears.vcs.VCSCommitMetadataBear import (VCSCommitMetadataBear,
                                             CommitResult, COMMIT_TYPE)
from bears.vcs.git.GitCommitMetadataBear import GitCommitMetadataBear
from coalib.settings.Section import Section
from coalib.testing.BearTestHelper import generate_skip_decorator


class FakeCommitBear(VCSCommitMetadataBear):
    @classmethod
    def check_prerequisites(cls):
        return True

    def get_head_commit_sha(self):
        return ('This is the fake head commit', '')


@generate_skip_decorator(VCSCommitMetadataBear)
class CommitBearTest(unittest.TestCase):

    def run_uut(self, *args, **kwargs):
        """
        Runs the unit-under-test (via `self.uut.run()`) and collects the
        messages of the yielded results as a list.

        :param args:   Positional arguments to forward to the run function.
        :param kwargs: Keyword arguments to forward to the run function.
        :return:       A list of the message strings.
        """
        return list(result.message for result in self.uut.run(*args, **kwargs))

    def setUp(self):
        self.msg_queue = Queue()
        self.section = Section('')
        self.uut = FakeCommitBear(None, self.section, self.msg_queue)

    def test_check_prerequisites(self):
        _shutil_which = shutil.which
        try:
            shutil.which = lambda *args, **kwargs: None
            self.assertEqual(GitCommitMetadataBear.check_prerequisites(),
                             'git is not installed.')

            shutil.which = lambda *args, **kwargs: 'path/to/git'
            self.assertTrue(GitCommitMetadataBear.check_prerequisites())
        finally:
            shutil.which = _shutil_which


class CommitResultTest(unittest.TestCase):
    def setUp(self):
        self.raw_commit_message = 'raw_commit_message'
        self.commit_sha = 'commit_sha'
        self.parent_commits = ['parent_commits']
        self.modified_files = ['modified_files']
        self.added_files = ['added_files']
        self.deleted_files = ['deleted_files']

    def test_commitresult_object_repr(self):
        repr_result = repr(CommitResult(VCSCommitMetadataBear,
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
