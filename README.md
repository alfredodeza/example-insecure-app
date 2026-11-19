# Securing Your Code on GitHub

A small bookmarks app, and the steps that let GitHub protect the repository it lives in:
push protection and secret scanning, a leaked key found in the history and rotated, code
scanning with CodeQL, Dependabot, an SBOM, and a test workflow pinned and limited to what
it needs.

The app starts with every weakness in place on purpose: an API key written in the code, a
search query built from what the user types, an older Flask, and a workflow with no
`permissions:` whose actions are referenced by tag. The app only ever runs on your own
computer, at `127.0.0.1:8005`. Never point these examples at a site you don't own.

## Setup

You need:

* [uv](https://docs.astral.sh/uv/), which installs Python 3.12 and the pinned packages
  (`uv sync`).
* Git, and the [GitHub CLI](https://cli.github.com) signed in with `gh auth login`.
* `curl`, `patch`, `jq` and OpenSSL (`openssl`), which most systems already have.
* [Gitleaks](https://github.com/gitleaks/gitleaks) 8.30.1, from its releases page or with
  `mise use gitleaks@8.30.1`.
* [Syft](https://github.com/anchore/syft), any recent release.

## Your own practice repository

This repository is the practice repository from the videos, with every change the lessons
make already in it. Every GitHub step happens in a repository of your own, so start from
its first version, tagged `start`: download
https://github.com/alfredodeza/example-insecure-app/archive/refs/tags/start.zip, unzip it, and in
that folder make an empty public repository on GitHub with your own account or org, then run
what "Creating a practice repository" types:

```bash
gh repo create <you>/example-insecure-app --public
git init -q -b main
git add .
git commit -m "First version of the bookmarks app"
git remote add origin git@github.com:<you>/example-insecure-app.git
git push -u origin main
```

## The lessons, in order

1. In the repository's Settings, Advanced Security: turn on Secret Protection and push
   protection.
2. Make a private key and try to push it (`openssl genpkey -algorithm ed25519 -out
   deploy-key.pem`, add, commit, `git push`): the push is refused. Take the commit back with
   `git reset HEAD~1` and delete the key file.
3. Move the API key out of the code before looking for it in the history: in `app.py`,
   add `import os` and replace the `API_KEY = "…"` line with
   `API_KEY = os.environ["PRACTICE_API_KEY"]`; put the old key in `.env` as
   `PRACTICE_API_KEY=<the old key>`; commit `app.py`. Then `gitleaks git --report-path
   leaks.json` finds the old key in the first commit.
4. Rotate it: `uv run make_key.py` writes a new key to `.env`, then
   `uv run --env-file .env app.py &` starts the app with it. The old key now gets `401`.
5. Turn on code scanning (default setup), read its alert, then
   `patch app.py fixes/parameterized-query.patch`, `uv run pytest -q`, commit and push.
6. Turn on Dependabot alerts and security updates, and merge its pull request for Flask.
7. `cp fixes/dependabot.yml .github/dependabot.yml`, commit and push.
8. `syft -q .` and `syft -q . -o spdx-json=sbom.json`.
9. `patch .github/workflows/tests.yml fixes/pin-actions.patch`, then
   `patch .github/workflows/tests.yml fixes/least-privilege.patch`, checking each with
   `uv run zizmor --offline .github/workflows/tests.yml`; then one
   `git commit -am "…"` and `git push`.
10. Tag a release (`git tag v1.0.0 && git push origin v1.0.0`); the release workflow builds
    and attests it. Then `grep -B1 -A2 actions/attest .github/workflows/release.yml`, `gh release download v1.0.0` and
    `gh attestation verify practice-bookmarks.tar.gz --repo <you>/example-insecure-app`.

`LESSONS.md` lists every command the videos type, in order. The app stops with `kill %1`.

## Tests

`uv run pytest -q` runs the app and its workflow checks at every step of the fixes, from
any point in the lessons. The same tests run on GitHub in `.github/workflows/tests.yml`.
