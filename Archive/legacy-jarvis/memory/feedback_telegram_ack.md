---
name: ""
metadata: 
  node_type: memory
  title: "Feedback: Telegram Task Acknowledgement"
  slug: feedback_telegram_ack
  type: feedback
  created: 2026-06-08T00:00:00+00:00
  tags: 
    - telegram
    - communication
    - channel-responder
  originSessionId: e6e7d446-30d0-4e98-9622-82f8d4ba5ead
---

# Telegram Task Acknowledgement

## Rule
When receiving a task via Telegram, always send an immediate ack message before starting work. Example: "On it — [one-liner of what I'm doing]"

## Why
Rob can't see Claude's internal narration or tool calls — only Telegram messages. A typing indicator alone is not enough signal that work has begun.

## How to Apply
Every channel-responder task message gets an immediate ack via `telegram-notify.sh` before any work begins. The ack should be short and specific: confirm receipt and name the action being taken.
