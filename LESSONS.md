# The commands from each lesson

Every command typed in the lesson videos, in order. Run them from the root of
this repository, after the setup in README.md.

## 2.1.2 Creating a practice repository

```bash
ls
git init -q -b main
git add .
git commit -m "First version of the bookmarks app"
gh repo view alfredodeza/example-insecure-app
git remote add origin git@github.com:alfredodeza/example-insecure-app.git
git push -u origin main
```

## 2.2.2 Pushing a secret and seeing it blocked

```bash
echo "https://hooks.slack.com/services/T…/B…/…" > slack-webhook.txt
git add slack-webhook.txt
git commit -m "Add the Slack webhook"
git push
git reset HEAD~1
git status --short
```

## 2.2.3 Finding a secret in a repository's history

```bash
grep -n API_KEY app.py
git log --oneline
gitleaks git --report-path leaks.json
jq '.[0] | {RuleID, File, StartLine, Commit}' leaks.json
```

## 2.2.4 Rotating a leaked practice key

```bash
uv run make_key.py
uv run --env-file .env app.py &
curl -i -H "X-API-Key: practice_key_4f1d8c2b9e7a6035d1c8" http://127.0.0.1:8005/bookmarks
source .env
curl -i -H "X-API-Key: $PRACTICE_API_KEY" http://127.0.0.1:8005/bookmarks
```

## 2.3.3 Fixing a code scanning alert

```bash
cat fixes/parameterized-query.patch
patch app.py fixes/parameterized-query.patch
uv run pytest -q
git commit -am "Use a parameterized query for search"
git push
```

## 3.1.6 Configuring Dependabot version updates

```bash
cp fixes/dependabot.yml .github/dependabot.yml
cat .github/dependabot.yml
git add .github/dependabot.yml
git commit -m "Check for updates every week"
git push
```

## 3.2.2 Creating an SBOM with Syft

```bash
syft -q .
syft -q . -o spdx-json=sbom.json
ls -l sbom.json
jq .spdxVersion sbom.json
```

## 3.3.2 Pinning actions to a commit

```bash
uv run zizmor --offline .github/workflows/tests.yml
git ls-remote https://github.com/actions/checkout refs/tags/v7.0.1
cat fixes/pin-actions.patch
patch .github/workflows/tests.yml fixes/pin-actions.patch
uv run zizmor --offline .github/workflows/tests.yml
```

## 3.3.4 Limiting a workflow's permissions

```bash
uv run zizmor --offline .github/workflows/tests.yml
cat fixes/least-privilege.patch
patch .github/workflows/tests.yml fixes/least-privilege.patch
uv run zizmor --offline .github/workflows/tests.yml
git commit -am "Pin the test workflow's actions and limit its token"
git push
```

## 3.4.3 Verifying a release attestation

```bash
grep -B1 -A2 actions/attest .github/workflows/release.yml
gh release download v1.0.0
ls -l practice-bookmarks.tar.gz
gh attestation verify practice-bookmarks.tar.gz --repo alfredodeza/example-insecure-app
echo changed >> practice-bookmarks.tar.gz
gh attestation verify practice-bookmarks.tar.gz --repo alfredodeza/example-insecure-app
```
