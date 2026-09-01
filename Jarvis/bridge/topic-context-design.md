# Topic-threaded conversation context (Rob's idea, 1 Sept 2026)

Status: design captured, not yet greenlit for build.

## The problem
The bridge feeds each run a flat tail of the last 16 lines of `conversation.log`
(`BUFFER_TURNS = 16` in `bridge.py`). Rob and I switch topics constantly (rope,
work, Tethered, family), so a topic's thread scrolls out of the buffer within a
few exchanges of switching away, even though the thread is still live. Rob's
framing: keep working context down to the conversation we're actually having,
with a complete, prioritised view of *that* thread, while parking the others.

## Rob's proposal (verbatim gist)
Per-topic context files. When we talk rope, that exchange is stored in a rope
thread and read back as priority context. Switch to work, the rope file gets
"saved" and a work thread takes over, still able to reference the old one.

## Recommended shape: tag-and-filter, not file-per-topic
Same effect, less machinery, no file lifecycle to manage:

1. **Tag at write time.** Each `conversation.log` line gets a topic slug
   (`[rope]`, `[work]`, `[tethered]`, `[general]`...). The responding run can do
   the tagging itself at the end of its turn (zero extra latency), or a cheap
   haiku call classifies the incoming message against the list of active slugs
   (adds ~1s and pennies per message).
2. **Filter at read time.** Context becomes:
   - last ~6 lines flat regardless of topic (so "yes, do that" still works and
     misclassification can't break the immediate exchange),
   - last ~20 lines of the matched topic thread (the "priority" context Rob
     wants),
   - a one-line index of other recent topics with their last-touched time
     ("also open: rope (this morning), tethered (Sun)") so the run knows what
     else is in flight and can pull a thread's tail if the message pivots.
3. **Rolling summaries later, if needed.** When a thread gets long, compress
   its head into a two-line summary kept at the top of the thread context.

## Design gotchas (why not naive file-per-topic)
- Messages that straddle two topics, or pure banter: needs a `general`
  catch-all and multi-tag tolerance.
- The flat recency window must survive: topic isolation without it breaks
  pronouns and short confirmations.
- Classifier drift: give the classifier the live slug list + last line of each
  thread, not a fixed taxonomy. New slugs allowed.
- Per-person: applies to Rob's log first; family logs could follow but stay
  private per existing rules.
- Relationship to the vault: topic threads are *working* memory (days-weeks);
  durable facts still get promoted to vault files as now. This is the missing
  middle layer between the 16-line buffer and the vault.

## Build estimate
A few hours in `bridge.py`: tagging (append-time), `recent_buffer()` becomes
topic-aware, one prompt-template change. Backfill: optional one-off haiku pass
over the existing log. Fully reversible (log format stays line-per-turn, tags
are a prefix).
