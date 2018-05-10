#!/usr/bin/python3

import git

g = git.cmd.Git('/opt/galaxymedia')
g.pull()
print(dir(git.cmd.Git))

# print(g.version_info)
"""
#repo = git.Repo('/opt/galaxymedia')

remote = git.Repo('https://github.com/cosmicc/galaxymedia.git')
#print(dir(git))
#print(repo.version_info)
#local_commit = repo.commit()
remote_commit = remote.fetch()[0].commit

commits_ahead = repo.iter_commits('origin/master..master')

count = sum(1 for c in commits_ahead)

print(count)
"""
