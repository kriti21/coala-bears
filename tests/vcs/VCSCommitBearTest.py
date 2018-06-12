import shutil
import unittest
import unittest.mock
from queue import Queue

from coalib.testing.BearTestHelper import generate_skip_decorator
from bears.vcs.VCSCommitBear import VCSCommitBear, CommitResult
from bears.vcs.git.GitCommitBear import GitCommitBear
from coalib.settings.Section import Section
from coalib.settings.Setting import Setting
from coalib.misc.Shell import run_shell_command
from coalib.testing.LocalBearTestHelper import get_results


class FakeCommitBear(VCSCommitBear):
    @classmethod
    def check_prerequisites(cls):
        return True

    def get_head_commit(self):
        return ('This is the fake head commit', '')

@generate_skip_decorator(VCSCommitBear)
class VCSCommitBearTest(unittest.TestCase):

    def run_uut(self):
        """
        Runs the unit-under-test (via `self.uut.run()`) and collects the
        messages of the yielded results as a list.

        :param args:   Positional arguments to forward to the run function.
        :param kwargs: Keyword arguments to forward to the run function.
        :return:       A list of the message strings.
        """
        return list(result.message for result in self.uut.run())

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

    def test_analyze_git_commit(self):
        run_shell_command('echo "a" >> testfile.txt ')
        run_shell_command('git add testfile.txt')
        run_shell_command('git commit -m "Add testfile"')

        result = get_results(self.uut, '')
        self.assertEqual(result.contents,
                         [''])


class CommitResultTest(unittest.TestCase):
    def setUp(self):
        self.commit_info = "commit analysis result str type"

    def test_commitresult_object_repr(self):
        repr_result = repr(CommitResult(VCSCommitBear,
            self.commit_info, 'HEAD commit information'))

        repr_regex = (
            r"<CommitResult object\(id=.+, origin=\'bearclass\', "
            r"message=\'HEAD commit information\', "
            r"contents=\[\'.+\'\]\) at .+>"
            )
        self.assertRegex(repr_result, repr_regex)
