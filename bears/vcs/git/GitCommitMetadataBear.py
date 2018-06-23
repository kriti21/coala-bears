from bears.vcs.VCSCommitMetadataBear import VCSCommitMetadataBear
from coalib.misc.Shell import run_shell_command


class COMMIT_TYPE(Flag):
    simple_commit = 0
    merge_commit = 1


class GitCommitMetadataBear(VCSCommitMetadataBear):
    LANGUAGES = {'Git'}

    @classmethod
    def check_prerequisites(cls):
        if shutil.which('git') is None:
            return 'git is not installed.'
        else:
            return True

    def analyze_commit(self, head_commit):
        raw_commit_message = head_commit

        get_head_commit = run_shell_command('git rev-parse HEAD')
        head_commit_sha = get_head_commit[0].strip('\n')

        commit_type = COMMIT_TYPE.simple_commit

        head_commit = head_commit.strip('\n')

        get_parent_commits = 'git log --pretty=%P -n 1 ' + _head_commit_sha
        all_parent_commits = run_shell_command(get_parent_commits)[0]
        parent_commits_list = all_parent_commits.split(' ')

        if len(parent_commits_list) >= 2:
            commit_type |= COMMIT_TYPE.merge_commit

        get_all_committed_files = ('git show --pretty="" --name-status ' +
                                   head_commit_sha)
        all_committed_files = run_shell_command(get_all_committed_files)[0]
        all_committed_files = all_committed_files.split('\n')

        modified_files_list = []
        added_files_list = []
        deleted_files_list = []

        for line in all_committed_files:
            pos = line.find('\t')
            change = line[:pos]
            if change == 'M':
                modified_files_list.append(line[pos+1:])
            elif change == 'A':
                added_files_list.append(line[pos+1:])
            elif change == 'D':
                deleted_files_list.append(line[pos+1:])

        return (raw_commit_message, head_commit_sha, parent_commits_list,
                commit_type, modified_files_list, added_files_list,
                deleted_files_list)
