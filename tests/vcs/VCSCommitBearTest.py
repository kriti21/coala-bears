import os
import platform
import shutil
import stat
import unittest
import unittest.mock
from queue import Queue
from tempfile import mkdtemp

from coalib.testing.BearTestHelper import generate_skip_decorator
from bears.vcs.VCSCommitBear import VCSCommitBear, CommitResult
from bears.vcs.git.GitCommitBear import GitCommitBear
from coalib.settings.Section import Section
from coalib.misc.Shell import run_shell_command


class FakeCommitBear(VCSCommitBear):
    @classmethod
    def check_prerequisites(cls):
        return True

    def get_head_commit(self):
        return ('This is the fake head commit', '')


@generate_skip_decorator(VCSCommitBear)
class VCSCommitBearTest(unittest.TestCase):

    @staticmethod
    def run_git_command(*args, stdin=None):
        run_shell_command(' '.join(('git',) + args), stdin)

    def run_uut(self, *args, **kwargs):
        """
        Runs the unit-under-test (via `self.uut.run()`) and collects the
        messages of the yielded results as a list.

        :param args:   Positional arguments to forward to the run function.
        :param kwargs: Keyword arguments to forward to the run function.
        :return:       A list of the message strings.
        """
        return list((result.message) for result in self.uut.run(*args, **kwargs))

    def assert_no_msgs(self):
        """
        Assert that there are no messages in the message queue of the bear, and
        show the messages in the failure message if it is not empty.
        """
        self.assertTrue(
            self.msg_queue.empty(),
            'Expected no messages in bear message queue, but got: ' +
            str(list(str(i) for i in self.msg_queue.queue)))

    def setUp(self):
        self.msg_queue = Queue()
        self.section = Section('')
        self.uut = FakeCommitBear(None, self.section, self.msg_queue)

        self._old_cwd = os.getcwd()
        self.gitdir = mkdtemp()
        os.chdir(self.gitdir)
        self.run_git_command('init')
        self.run_git_command('config', 'user.email coala@coala.io')
        self.run_git_command('config', 'user.name coala')

    def test_check_prerequisites(self):
        _shutil_which = shutil.which
        try:
            shutil.which = lambda *args, **kwargs: None
            self.assertEqual(GitCommitBear.check_prerequisites(),
                             'git is not installed.')

            shutil.which = lambda *args, **kwargs: 'path/to/git'
            self.assertTrue(GitCommitBear.check_prerequisites())
        finally:
            shutil.which = _shutil_which

    def test_head_commit(self):
        self.assertEqual(self.run_uut(), ['HEAD commit information'])


@generate_skip_decorator(GitCommitBear)
class AnalyzeGitCommitTest(unittest.TestCase):

    @staticmethod
    def run_git_command(*args, stdin=None):
        run_shell_command(' '.join(('git',) + args), stdin)

    def run_uut(self, *args, **kwargs):
        """
        Runs the unit-under-test (via `self.uut.run()`) and collects the
        messages of the yielded results as a list.

        :param args:   Positional arguments to forward to the run function.
        :param kwargs: Keyword arguments to forward to the run function.
        :return:       A list of the message strings.
        """
        return list((result.raw_commit_message,
            result.commit_sha,
            result.commit_type,
            result.added_files,
            result.modified_files,
            result.deleted_files) for result in self.uut.run(*args, **kwargs))


    def assert_no_msgs(self):
        """
        Assert that there are no messages in the message queue of the bear, and
        show the messages in the failure messgae if it is not empty.
        """
        self.assertTrue(
            self.msg_queue.empty(),
            'Expected no messages in bear message queue, but got: ' +
            str(list(str(i) for i in self.msg_queue.queue)))

    def setUp(self):
        self.msg_queue = Queue()
        self.section = Section('')
        self.uut = GitCommitBear(None, self.section, self.msg_queue)

        self._old_cwd = os.getcwd()
        self.gitdir = mkdtemp()
        os.chdir(self.gitdir)
        self.run_git_command('init')
        self.run_git_command('config', 'user.email coala@coala.io')
        self.run_git_command('config', 'user.name coala')

    @staticmethod
    def _windows_rmtree_remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def tearDown(self):
        os.chdir(self._old_cwd)
        if platform.system() == 'Windows':
            onerror = self._windows_rmtree_remove_readonly
        else:
            onerror = None
        shutil.rmtree(self.gitdir, onerror=onerror)

    def test_analyze_git_commit(self):
        run_shell_command('git checkout -b testbranch master')
        run_shell_command('touch testfile1.txt ')
        run_shell_command('git add testfile1.txt')
        run_shell_command('git commit -m "Add testfile1"')
        test_sha1 = run_shell_command('git rev-parse HEAD')[0].strip('\n')
        self.assertEqual(self.run_uut(),
            [('Add testfile1\n\n', test_sha1, ['merge_commit'],
             ['testfile1.txt'], [], [])])

        run_shell_command('touch testfile2.txt ')
        run_shell_command('git add testfile2.txt')
        run_shell_command('git commit -m "Add testfile2 [ci skip]"')
        test_sha2 = run_shell_command('git rev-parse HEAD')[0].strip('\n')
        self.assertEqual(self.run_uut(),
            [('Add testfile2 [ci skip]\n\n', test_sha2, ['ci_skip_commit',
                'merge_commit'], ['testfile2.txt'], [], [])])

        run_shell_command('touch testfile3.txt ')
        self.run_git_command('add', 'testfile3.txt')
        self.run_git_command('commit', '-m', '"another commit [skip ci]"')
        test_sha3 = run_shell_command('git rev-parse HEAD')[0].strip('\n')
        self.run_git_command('revert', 'HEAD', '--no-edit')
        test_sha4 = run_shell_command('git rev-parse HEAD')[0].strip('\n')
        test_raw_commit_msg = ('Revert "another commit [skip ci]"' +
            '\n\nThis reverts commit ' + test_sha3 + '.\n\n')
        self.assertEqual(self.run_uut(),
            [(test_raw_commit_msg, test_sha4,
             ['ci_skip_commit', 'merge_commit'], [], [], ['testfile3.txt'])])

        run_shell_command('git checkout master')
        run_shell_command('git checkout -b new-feature master')
        run_shell_command('touch testfile4.txt ')
        self.run_git_command('add', 'testfile4.txt')
        self.run_git_command('commit', '-m', '"Commit in feature branch"')
        run_shell_command('git checkout master')
        run_shell_command('git merge --no-ff new-feature')
        test_raw_commit_msg = "Merge branch 'new-feature'\n\n"
        test_sha5 = run_shell_command('git rev-parse HEAD')[0].strip('\n')
        self.assertEqual(self.run_uut(),
            [(test_raw_commit_msg, test_sha5,
            ['merge_commit'], [], [], [])])


class CommitResultTest(unittest.TestCase):
    def setUp(self):
        self.raw_commit_message = 'raw_commit_message'
        self.commit_sha = 'commit_sha'
        self.commit_type = ['commit_type']
        self.modified_files = ['modified_files']
        self.added_files = ['added_files']
        self.deleted_files = ['deleted_files']

    def test_commitresult_object_repr(self):
        repr_result = repr(CommitResult(VCSCommitBear,
                                        self.raw_commit_message,
                                        self.commit_sha,
                                        self.commit_type,
                                        self.modified_files,
                                        self.added_files,
                                        self.deleted_files,))

        repr_regex = (
            r"<CommitResult object\(id=.+, origin=\'bearclass\', "
            r"raw_commit_message=\'.+\', "
            r"commit_sha=\'.+\', "
            r'commit_type=\[.+\], '
            r'modified_files=\[.+\], '
            r'added_files=\[.+\], '
            r'deleted_files=\[.+\], '
            r"message=\'HEAD commit information\'\) at .+>"
            )
        self.assertRegex(repr_result, repr_regex)
