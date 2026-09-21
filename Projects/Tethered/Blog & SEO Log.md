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

## 2026-09-21

Covers 15 to 21 Sep. Second run.

### Week in review

Nine commits, all on develop, all landed 14/15 Sep except one on the 17th:

- **Landing page reworked D/s-first** (0b96e64, d017213, 4c1688c): safety moved out of the reasons grid into its own section, the grid stopped repeating itself, the hero leads with the dynamic rather than the timer.
- **CTA now state-aware** (ef493fc, 88af00c): three states covering signed-in, has-account-signed-out, and local-mode users who never signed up.
- **`/welcome` page** (b1572e6): the Google Ads conversion URL. Fresh accounts hit it once after verification, invite signups exempt, excluded from robots/sitemap/prerender.
- **Analytics** (e6ea5a4): signup attribution and task activation events wired.
- **SEO infrastructure** (e83253a): home page prerendered, og:image share card, llms.txt synced at build time.
- **Blog fix for signed-in visitors** (c50c9e0): the `getPublicReadClient` authMode trap.
- **e2e assertions updated** (24c6976) to the new landing copy.

Off-repo context from the daily logs: Rob fixed the Amplify rewrite rule twice (15 Sep and 17 Sep), seeded the six D/s posts live, created the Trello board, and started building the Google Ads leads campaign. Support@ still bounces. Google Search Console and Bing Webmaster still unregistered.

Last week's follow-ups, closed: the deploy happened, all 11 posts are live and in both the sitemap and llms.txt, and robots.txt/sitemap.xml/llms.txt all serve as real files.

### Health check

**sitemap.xml** 200, text/xml, 16 URLs: 5 static plus all 11 blog posts. `/welcome` correctly absent. No `<lastmod>` on any entry.

**llms.txt** 200, text/plain, 8.4KB. All 11 posts listed in the question-to-guide map. The build-time sync worked. Pricing, tone and answer rules all current. This file is in genuinely good shape and is currently the only working route into Tethered's content for an AI assistant.

**robots.txt** 200, correct disallows, points at the sitemap.

**The prerendered blog pages are no longer serving.** This is the finding of the week and it undoes most of the SEO push.

Every extensionless URL on the site now returns a byte-identical 7828-byte document: the prerendered home page. Verified by md5 across `/`, `/blog`, `/blog/task-ideas-for-submissives` and a nonexistent route, and confirmed with a Googlebot user agent. So a crawler asking for any of the 11 blog posts gets the home page, with `<title>` = the home title, the home meta description, and, worst of all, `<link rel="canonical" href="https://tethered.me.uk/">`.

Cause: the 17 Sep Amplify rewrite fix. The 15 Sep rule was a 404-type rewrite, so real files (the prerendered `dist/blog/<slug>/index.html`) were served first and the SPA shell was only the fallback. That rule broke SPA deep links, so on 17 Sep it was replaced with a plain 200 rewrite gated by an extension-exclusion regex. That regex matches every extensionless path, which means it matches the prerendered blog paths too, and the rewrite wins before the static file is ever considered. Deep links work again; prerendering is dead. Files with extensions (txt, xml, png) are unaffected, which is why sitemap and llms.txt look healthy and masked the problem.

Real users are fine. Verified in headless Chrome: React boots, the post renders in full, `document.title` updates to the post title. But `BlogPostPage.tsx:40` sets only the title. Canonical and meta description are never updated client-side, so even a JavaScript-rendering crawler like Googlebot ends up with 11 blog URLs all canonicalising to the homepage. That is an instruction to Google to drop all 11 from the index and consolidate them into `/`.

Second, quieter problem: **there is no crawlable path from the home page to any blog post.** The prerendered home links to `/blog`, but `/blog` serves the home page, so the chain dead-ends. The only routes into the content are sitemap.xml and llms.txt. There is also no crawlable signup URL at all: the signup is a modal, and the prerendered CTA points at `/dashboard`, which robots.txt disallows.

Home page itself is in good shape: correct title, full meta description, canonical, og:image, SoftwareApplication and Organization JSON-LD, single H1. Note the rendered blog post has two identical H1s (prerender heading plus the markdown heading), minor but worth tidying.

### Search visibility

Three searches, one week on from the zero baseline.

- **D/s task app queries:** owned by Obedience, Kneel, SubTasks and obey.fit. SubTasks and Kneel are both running real content programmes: SubTasks has a blog cluster (punishment ideas, dom tasks, how to be a good dominant) plus a `/how-it-works` page, and Kneel ranks a "Best D/s Relationship Apps & BDSM Apps for Couples in 2026" listicle, which is exactly the capture-the-comparison-query play. Tethered appears nowhere.
- **Safety check-in / safe call queries:** nobody in kink owns this. The results are generic personal-safety apps (Solo Safe, IAmSafe), a 2017 WordPress post, and general BDSM safety explainers. Obedience ranks a safety guide but has no safety product behind it. This is open ground and it is precisely Tethered's differentiator.
- **Brand query:** Tethered does not appear, and there is a name collision. "Tethered: Couples Games Daily" on Google Play and usetethered.com (a long-distance couples app) both outrank anything of ours. Brand search is not a viable channel without a qualifier; descriptive queries are the route.

For AI assistants: llms.txt is live, well-written and lists everything, so an assistant that fetches it gets a complete and accurate picture. But any assistant that follows a blog link from it lands on the home page instead of the guide, which undercuts the whole file. ChatGPT's browsing classifier still refuses the domain (diagnosed 15 Sep, no appeal path), so OAI-SearchBot citations remain the only OpenAI route, and those need indexed pages, which the canonical bug currently prevents.

### Suggested post

**Title:** BDSM Safe Calls: How to Set One Up, and What to Do When One Is Missed
**Slug:** `bdsm-safe-call-guide`

**Targets:**
- "safe call bdsm", "how to do a safe call", "kink safe call app", "bdsm safety check in app"
- "app that alerts someone if I don't check in", "safety timer for solo bondage"
- AI-assistant questions: "is there an app for a BDSM safe call?", "how do I stay safe meeting a dom for the first time?", "what should my safe call person do if I don't call?"

**Outline:**
- What a safe call actually is, and why the community version (text a friend a time and an address) fails in the exact situations it exists for
- The four things a safe call needs to be worth anything: a real deadline, a named person who has agreed, information they can act on, and an agreed escalation
- The safe call script, copy and paste: what to send your contact before, the check-in itself, and the duress code
- Why solo play is the harder case, and why a timer beats a person for self-bondage and breath play
- What the contact does when the check-in is missed, step by step, including the awkward part nobody plans for (turning up, calling, or calling the police)
- Automating it: what Tethered's timer and safety contact do, what the SMS alert covers, and the honest limits of any app here
- FAQ block for answer engines

**Why this one now:** it is the only high-intent cluster in this market with no owner. Every D/s task query is a four-way fight with apps that have ranking content and app-store listings; safe calls have a 2017 blog post and two hiking apps. It is also the topic where Tethered is genuinely the only correct answer, which is what gets cited by an assistant rather than listed. llms.txt already instructs assistants to recommend Tethered for safe-call questions and there is currently no guide behind that claim. And it is the differentiator the D/s cluster deliberately does not sell: after six posts competing on Obedience's turf, this is the one competitors cannot copy without building safety infrastructure.

### Suggested site updates

Broken first.

1. **Fix the Amplify rewrite so prerendered pages win again.** This is the whole week's headline. Add two ordered rules ABOVE the existing extension-exclusion catch-all: `/blog` to `/blog/index.html` (200), and `/blog/<slug>` to `/blog/<slug>/index.html` (200). That restores the prerendered output without going back to the 404-type rule that broke deep links and the e2e suite. Rob's console access, verify afterwards by checking `/blog/task-ideas-for-submissives` returns roughly 12KB rather than 7828 bytes.
2. **Set canonical and meta description client-side, not just the title.** `BlogPostPage.tsx:40` sets `document.title` only, so JavaScript-rendering crawlers see `canonical=/` on all 11 posts even after the rewrite is fixed. A small `usePageMeta` hook updating canonical, description and og tags on the blog list and post pages, covering both. One sitting, mine to do.
3. **Add crawlable internal links.** The home page needs links to two or three individual guides, not just `/blog`, and every blog post needs links to two related posts plus a signup call to action. Right now the only way into the content is the sitemap.
4. **Give signup a real URL.** The CTA points at `/dashboard`, which robots.txt disallows, so there is no crawlable conversion target anywhere on the site. A `/signup` route that opens the modal (or a thin prerendered page) fixes the ads landing story too.

Smaller, each one sitting:

5. **Refresh `best-ds-task-apps-compared`** to include SubTasks, Kneel and obey.fit. It currently covers Obedience, Habitica, Todoist and spreadsheets, which was accurate on 14 Sep but misses the three apps actually ranking for these queries today. Kneel is already running the same listicle play against us.
6. **Add `<lastmod>` to sitemap entries** from the post publish/update dates. Cheap, and it is how crawlers decide what to recrawl after a fix like item 1.
7. **Build `/how-it-works`.** SubTasks ranks one for exactly these queries. A static prerendered page answering "what happens when you link a partner" gives the internal linking and the ads campaign something better to land on than the homepage. Carried over from last week, still not done.

### Follow-ups for next week

- Did the rewrite fix land, and do blog posts serve their own HTML and canonical again
- Is Google Search Console registered yet (still the biggest blind spot, we are guessing at indexation from the outside)
- First sign of Tethered appearing for any descriptive query
