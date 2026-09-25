# Restoring session context after losing the head node

This directory exists only on the branch `snapshot/2026-09-25-main`. It was
taken on 2026-09-25 at about 08:40 UTC. Start with
`docs/handover-2026-09-25-paper-session.md`, which says what was running, what
the paper draft looks like and what is still open.

## Claude Code memory

`claude-memory/` is a copy of Claude Code's auto-memory for this project.
Claude Code keeps it at

    ~/.claude/projects/-home-laievan-chia-hackathon-paper-to-pipeline/memory/

That directory name encodes the clone's absolute path. On a new machine with
the clone at the same path (`/home/laievan/chia-hackathon/paper-to-pipeline`),
copy the files back:

    mkdir -p ~/.claude/projects/-home-laievan-chia-hackathon-paper-to-pipeline/memory
    cp session-context/claude-memory/*.md \
       ~/.claude/projects/-home-laievan-chia-hackathon-paper-to-pipeline/memory/

If the clone lives at a different path, replace every `/` in that path with
`-` to get the directory name.

## What is not here

- Session transcripts (`~/.claude/projects/.../*.jsonl`). They contain live
  credentials (a gateway token, Google OAuth access tokens, API keys), so they
  were not committed.
- `third_party/`. Rebuild it with `scripts/fetch_artifacts.sh` and
  `scripts/build_gem5_workloads.sh`.
- Traces. Workers download them during `chia up` (see `cluster/cluster.yaml`).

## The run artifacts

`out/` was force-added to this snapshot, even though `.gitignore` excludes it.
So on this branch it is tracked. Before merging the branch into `main`, move
what is worth keeping into `runs/<date>-<host>/` (the convention the existing
`runs/` READMEs follow) and drop `out/` from the merge.
