# Tethered: Blog & SEO Log

Weekly review of Tethered's content and search visibility (cron: `Jarvis/bin/blog-suggest.sh`, Mondays 10:00). One dated section per run: health check findings, the blog post pitch, and the suggested site updates. Suggestions only, nothing here is auto-published.

## 2026-09-14

First run. Covers the SEO push shipped on 13/14 Sep.

### Week in review

Eight commits, all SEO/content, all landed 14 Sep:

- `9011711` llms.txt draft, `56d977d` explicit title/meta/OG + hero copy
- `b8dd48d` repositioned the whole site as a D/s dynamic management app (tasks/rewards/punishments first, safety as the differentiator)
- `6deb539` build-time sitemap.xml generator + robots.txt
- `e29557c` six new blog posts targeting D/s keywords
- `4010fc8` build-time prerender of public blog pages
- `34d715d` llms.txt rewritten around partner-linking
- `1387ce8` seed script now upserts by slug instead of blind-inserting

Content inventory is now 11 posts in `scripts/blog-posts/`: five original safety-cluster guides (solo play, meeting partners, consent negotiation, when things go wrong, plus a Fireplay post that exists only in the live database and not in the repo), and six new D/s-cluster posts (task ideas, setting rules, rewards/punishments, contract guide + template, task app comparison, long distance).

### Health check: the headline problem

**Production is five commits behind develop, and the entire SEO push is in those five commits.** `main` is at `b8dd48d`; everything after it is unreleased. Live consequences, all verified by curl this morning:

| Check | Result |
|---|---|
| `/sitemap.xml` | **404** |
| `/robots.txt` | **404** (zero bytes) |
| `/llms.txt` | 200, but it is the `b8dd48d` version, not the partner-focused rewrite |
| `/blog` and every post URL | 200 but serves the 1621-byte SPA shell, no prerendered content |
| Six new D/s posts | Not live (also still need `seed-blog-posts.ts production`, which needs Rob's AWS creds) |

So the sitemap the robots file would point at does not exist, the robots file does not exist either, and the one artefact that does serve (llms.txt) advertises five safety guides and none of the new commercial content. From a crawler's point of view last week shipped nothing.

Separately, `/llms.txt` serving correctly confirms Rob's earlier Amplify rewrite fix worked for `.txt`. The `xml` exclusion cannot be confirmed either way yet because there is no sitemap file to serve; it will need re-checking after the deploy rather than assumed fixed.

### Health check: page-level

Home page meta is genuinely good now: title "Tethered | D/s Task, Reward & Punishment App for BDSM Dynamics", a full description, og:title/description/url. Missing from the head: `rel=canonical`, `og:image` (so every share and every social card is blank), twitter card tags, and JSON-LD.

The real page-level issue is that the body is `<div id="root"></div>` and nothing else. No H1, no crawlable internal links at all: not to the blog, not to signup, not between pages. Every "internal linking" question is moot until prerendering is live. Note that `scripts/prerender.ts` only covers `/blog` and `/blog/<slug>`, so even after it deploys the home page stays an empty shell for non-JS crawlers, which is exactly the page an AI assistant would want to read before citing the product.

### Health check: who ranks, and would an LLM cite Tethered

Searched the audience's actual queries. Short answer: Tethered does not appear anywhere, and the competitive set is more developed than the positioning work assumed.

For D/s task apps, the field is SubTasks (subtasksapp.com), Kneel (getkneel.com), Obedience (obedienceapp.com) and obey.fit. These are not just app listings, they are content operations: SubTasks and Kneel both run blogs targeting the same keywords Tethered just wrote for, and SubTasks ranks a `/how-it-works` page directly in the results.

The "obedience app alternative" SERP is fully contested: Kneel has a dedicated alternatives page, SubTasks has "Free Alternatives to Obedience App", KNKI has a tested-and-ranked roundup, plus alternativeto.net and the app-alternative aggregators. Tethered has exactly the right page written for this (`best-ds-task-apps-compared`) and it is sitting unpublished in the repo. This is the single highest-value unpublished asset.

Useful competitive fact from those results: SubTasks is aggressively free (unlimited tasks, photo proof, no premium tier), Kneel is $79.99/yr covering both partners, Obedience is roughly $14/month per person with a 5-habit free cap. Tethered's free tier is 5 tasks and 1 checklist profile, which is the Obedience shape, not the SubTasks shape. Worth knowing before the paywall lands.

On the safety side, the competitors are generic: Still Safe and Solo Safe are non-kink check-in apps, and the BDSM task apps have no safety layer at all (Kneel's "daily wellness check-ins" is the closest anyone gets). **The intersection of D/s management and real safety tooling is genuinely unoccupied.** That is Tethered's defensible position and nothing currently published says so.

Would an LLM cite Tethered today? No. It would find llms.txt (good, and well written), then follow every link in it to a blank SPA shell and have nothing to quote. llms.txt is doing its job and the site behind it is not.

### Blog post pitch

**Title:** D/s Check-Ins: How to Know Your Submissive Is Actually Okay

**Slug:** `ds-check-ins-guide`

**Targets:** "how to check in with your submissive", "D/s daily check in questions", "wellness check in D/s dynamic", "sub drop check in", "how do I know my sub is okay". AI-assistant phrasings: "what questions should a Dom ask in a daily check-in", "how do I tell if my submissive is struggling", "is my sub okay or just being obedient".

**Outline:**

- Why compliance is not the same as wellbeing: a sub who completes every task can still be sinking, and task-completion data hides it by design
- The three check-in types and what each is for: the daily temperature check, the post-scene check, and the 48-hour drop check
- Actual questions that work, with the ones that do not (anything answerable with "yes, Sir" is not a check-in)
- Building it into the dynamic as structure rather than an interruption: cadence, who initiates, what happens when a check-in is missed
- Distance and asynchronous dynamics: check-ins when you cannot read the room
- When a check-in surfaces something real: escalation, pausing the dynamic, and where a safety contact fits
- FAQ block for answer engines

**Why this one now:** every one of the six posts that shipped last week sells the management half of the product, and none of them sells the half competitors cannot copy. Kneel is already marketing "daily wellness check-ins" as a premium feature, which proves the demand without anyone owning the topic. It is also the cleanest possible funnel into the paywall pivot: a check-in protocol is worthless solo, so the call to action is "link your partner", which is exactly what the paywall gates on. It bridges the new D/s cluster back to the five existing safety guides, which gives the site its first real internal link structure.

### Suggested site updates

Broken first.

1. **Merge develop to main and deploy.** Five commits, already green (tsc, 476 tests, build) and already reviewed. Everything below is blocked behind it. This is the whole week's work sitting on the shelf.
2. **Run `seed-blog-posts.ts production`** to publish the six D/s posts. Needs Rob's AWS creds. The upsert-by-slug fix in `1387ce8` means this is now safe to re-run.
3. **Re-check `/sitemap.xml` after the deploy.** If it serves index.html rather than XML, the `xml` exclusion is still missing from the Amplify rewrite list. If it 404s, the generator did not run. Also confirm `/robots.txt` serves, it is currently a 404 and it is the file pointing crawlers at the sitemap.
4. **Regenerate llms.txt after seeding** so it lists all eleven posts. It currently advertises five, and the six commercial posts are invisible to exactly the AI assistants llms.txt exists to serve. Worth making this a build step alongside the sitemap rather than a hand-maintained file that drifts every time a post ships.

Smaller improvements, each one sitting:

5. **Add `og:image`, `rel=canonical` and JSON-LD to the home page head.** Every share of tethered.me.uk currently renders a blank card. The blog posts already get JSON-LD from the prerender script; the home page gets nothing.
6. **Extend `prerender.ts` to the home page.** Same script, one more output: a real H1, the feature copy, and crawlable links to /blog and signup. Currently the most important page on the site is invisible to anything that does not run JavaScript.
7. **Build a `/how-it-works` page.** SubTasks ranks one today for these exact queries. It is a static page answering "what happens when you link a partner", and it gives the sitemap and the internal linking something to point at besides blog posts.

### Follow-ups for next week

- Did the deploy happen, and do sitemap/robots/llms.txt all serve correctly
- Are the six D/s posts live and prerendered (check byte size of a post URL, the shell is 1621 bytes)
- First check for Tethered appearing in any of the three competitive searches
