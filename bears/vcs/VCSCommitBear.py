import abc

from coalib.bears.GlobalBear import GlobalBear
from coalib.results.HiddenResult import HiddenResult
from coalib.results.Result import Result
from coalib.misc.Shell import run_shell_command


class CommitResult(HiddenResult):
    def __init__(self, origin, commit_info, message):
        Result.__init__(self, origin, commit_info)
        self.contents = [commit_info]
        self.message = message


class VCSCommitBear(GlobalBear):
    __metaclass__ = abc.ABCMeta
    LANGUAGES = {'Git'}
    AUTHORS = {'The coala developers'}
    AUTHORS_EMAILS = {'coala-devel@googlegroups.com'}
    LICENSE = 'AGPL-3.0'

    @abc.abstractmethod
    def get_head_commit(self):
        """
        Return the commit message from the head commit
        """

    def analyze_git_commit(self, stdout):
        commit_info = dict()
        commit_info['raw_commit_message'] = stdout

        commit_sha = run_shell_command('git rev-parse HEAD')[0].strip('\n')

        commit_type = []

        stdout = stdout.strip('\n')

        if 'ci skip' in stdout or 'skip ci' in stdout: ##
            commit_type.append('ci_skip_commit')

        get_parent_commits = 'git log --pretty=%P -n 1 ' + commit_sha
        parent_commits, _ = run_shell_command(get_parent_commits)
        parent_commits_list = parent_commits.split('\n')

        if len(parent_commits_list) > 2:
            commit_type.append('merge_commit')

        get_all_committed_files = 'git show --pretty="" --name-status ' + commit_sha
        all_committed_files, _ = run_shell_command(get_all_committed_files)
        all_committed_files = all_committed_files.split('\n')

        modified_files_list = []
        added_files_list = []
        deleted_files_list = []

        for file in all_committed_files:
            pos = file.find('\t')
            change = file[:pos]
            if change == 'M':
                modified_files_list.append(file[pos+1:])
            elif change == 'A':
                added_files_list.append(file[pos+1:])
            elif change == 'D':
                deleted_files_list.append(file[pos+1:])

        commit_info['commit_sha'] = commit_sha
        commit_info['commit_type'] = commit_type
        commit_info['modified_files'] = modified_files_list
        commit_info['added_files'] = added_files_list
        commit_info['deleted_files'] = deleted_files_list

        return str(commit_info)

    def run(self):
        stdout, _= self.get_head_commit()

        commit_info = self.analyze_git_commit(stdout)

        yield CommitResult(self, commit_info, 'HEAD commit information')
