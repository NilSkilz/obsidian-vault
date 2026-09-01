#!/usr/bin/env python3
"""One-off backfill: tag the existing conversation.log entries with topic slugs
so the topic-threaded context (topic-context-design.md) starts with history
instead of an empty set of threads.

Groups the log into entries, classifies untagged ones in batches via a cheap
haiku call, and rewrites the log atomically. The bridge may append while this
runs, so the rewrite checks the file hasn't diverged from what was read and
carries any lines appended in the meantime over untagged (they only lose thread
membership, never content). A timestamped .bak copy is taken first.

Usage: python3 backfill_topics.py [--dry-run] [path-to-log]
"""
import json
import pathlib
import re
import subprocess
import sys
import time

import bridge  # entry_start/TOPIC_RE live there; keeps the two parsers identical

BATCH = 30
NAMES = ("Rob", "Jarvis")
SEED_SLUGS = ["general", "rope", "work", "tethered", "tide", "haven", "craft-erp",
              "saline-pump", "infra", "estim", "scorpion", "contract-hunt", "health",
              "family", "mary", "fuck-io", "jarvis-dev"]


def group_raw(lines):
    """Entries as {"topic", "raw" (original lines), "head" (first line, tag stripped)}."""
    entries = []
    for line in lines:
        st = bridge.entry_start(line, NAMES)
        if st is not None:
            entries.append({"topic": st[0], "raw": [line], "head": st[1]})
        elif entries:
            entries[-1]["raw"].append(line)
        else:
            entries.append({"topic": None, "raw": [line], "head": line})
    return entries


def classify_batch(batch, slugs, context_tail):
    items = []
    for i, e in enumerate(batch):
        snip = " ".join(e["head"].split())[:160]
        extra = ""
        if len(e["raw"]) > 1:
            extra = " | " + " ".join(e["raw"][1].split())[:80]
        items.append(f"{i}. {snip}{extra}")
    prompt = (
        "You tag chat log entries with topic slugs so the log can be read as threads.\n\n"
        "Slugs already in use (reuse these wherever they fit, mint new lowercase-kebab-case "
        "slugs of max 20 chars only for genuinely new subjects; use general for greetings "
        "and banter):\n" + ", ".join(sorted(slugs))
        + ("\n\nThe entries directly before this batch were tagged:\n" + context_tail if context_tail else "")
        + "\n\nEntries to tag, in conversation order (a short reply usually continues the "
        "topic of the entry above it):\n" + "\n".join(items)
        + f"\n\nOutput EXACTLY {len(batch)} lines, one slug per line, in order, nothing else."
    )
    proc = subprocess.run(
        [bridge.CLAUDE_BIN, "-p", prompt, "--model", bridge.CLASSIFY_MODEL, "--allowedTools", ""],
        capture_output=True, text=True, timeout=120, cwd="/tmp",
    )
    out = [l.strip().strip("`\"'.").lower() for l in (proc.stdout or "").splitlines() if l.strip()]
    if len(out) != len(batch) or not all(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,23}", s) for s in out):
        return None
    return out


def main():
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = pathlib.Path(args[0]) if args else bridge.CONVO
    orig_lines = path.read_text().splitlines()
    entries = group_raw(orig_lines)
    todo = [e for e in entries if e["topic"] is None]
    print(f"{len(entries)} entries, {len(todo)} untagged")
    slugs = set(SEED_SLUGS) | {e["topic"] for e in entries if e["topic"]}
    done_tail = []
    for start in range(0, len(todo), BATCH):
        batch = todo[start:start + BATCH]
        got = None
        for attempt in (1, 2):
            try:
                got = classify_batch(batch, slugs, "\n".join(done_tail[-3:]))
            except Exception as ex:
                print(f"batch {start // BATCH}: error {ex}")
            if got:
                break
        if not got:
            print(f"batch {start // BATCH}: unusable output twice, leaving untagged")
            continue
        for e, slug in zip(batch, got):
            e["topic"] = slug
            slugs.add(slug)
            done_tail.append(f"[{slug}] {' '.join(e['head'].split())[:80]}")
        print(f"batch {start // BATCH}: tagged {len(batch)}")
    new_lines = []
    for e in entries:
        head = e["head"] if e["topic"] is None else f"[{e['topic']}] {e['head']}"
        new_lines.append(head)
        new_lines.extend(e["raw"][1:])
    if dry:
        print("\n".join(new_lines[-40:]))
        return
    bak = path.with_suffix(f".bak-{time.strftime('%Y%m%d-%H%M%S')}")
    bak.write_text("\n".join(orig_lines) + "\n")
    # Atomic swap with growth check: anything appended since we read goes over untagged.
    current = path.read_text().splitlines()
    if current[:len(orig_lines)] != orig_lines:
        print("log diverged (not just appended); aborting, .bak kept")
        return
    new_lines.extend(current[len(orig_lines):])
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(new_lines) + "\n")
    tmp.replace(path)
    counts = {}
    for e in entries:
        counts[e["topic"]] = counts.get(e["topic"], 0) + 1
    print("done. topic counts:", json.dumps(counts, indent=0, sort_keys=True))


if __name__ == "__main__":
    main()
