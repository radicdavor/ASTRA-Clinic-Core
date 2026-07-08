# Program 1 Phase K0 - Remote Push Tag Verification

This document records the remote branch and tag verification for `program-1-pilot-demo-rc1`.

## Remote Main Verification

Commands run:

```bash
git fetch origin
git status -sb
git log --oneline origin/main..main
git log --oneline main..origin/main
git rev-list --left-right --count origin/main...main
git ls-remote --heads origin main
```

Captured results:

```text
git fetch origin
# no output

git status -sb
## main...origin/main

git log --oneline origin/main..main
# no output

git log --oneline main..origin/main
# no output

git rev-list --left-right --count origin/main...main
0    0

git ls-remote --heads origin main
06b746468957662bab47b93b964028189d9cdeff    refs/heads/main
```

Outcome:

- `main` is aligned with `origin/main`
- no local ahead commits remain
- no unexpected remote-only commits remain
- working tree was clean at verification start

## Remote Tag Verification

Commands run:

```bash
git fetch --tags origin
git tag --list "program-1-pilot-demo-rc1"
git show --stat program-1-pilot-demo-rc1
git ls-remote --tags origin program-1-pilot-demo-rc1
git rev-parse program-1-pilot-demo-rc1
git rev-parse 'program-1-pilot-demo-rc1^{}'
```

Captured results:

```text
git fetch --tags origin
# no output

git tag --list "program-1-pilot-demo-rc1"
program-1-pilot-demo-rc1

git show --stat program-1-pilot-demo-rc1
tag program-1-pilot-demo-rc1
Tagger: Davor Radic <radicdavor@gmail.com>
Date:   Wed Jul 8 20:08:34 2026 +0200

Program 1 Pilot Demo RC1

commit 06b746468957662bab47b93b964028189d9cdeff

git ls-remote --tags origin program-1-pilot-demo-rc1
27ef17a625751fc057e886e025fa113705dd3ec7    refs/tags/program-1-pilot-demo-rc1

git rev-parse program-1-pilot-demo-rc1
27ef17a625751fc057e886e025fa113705dd3ec7

git rev-parse 'program-1-pilot-demo-rc1^{}'
06b746468957662bab47b93b964028189d9cdeff
```

Outcome:

- tag exists locally
- tag exists on origin
- tag is annotated
- tag points to the intended Program 1 Pilot Demo RC1 commit state
- tag is a release-candidate marker, not production approval
