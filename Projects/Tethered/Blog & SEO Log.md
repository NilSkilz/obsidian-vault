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

## 2026-09-28

Covers 22 to 28 Sep. Third run.

### Week in review

**No commits. Nothing shipped.** `develop` is still at `24c6976` (17 Sep), and the handoff file the cron passes me (`/tmp/jarvis-blog-suggest.rTme2j`) was empty, which is accurate rather than broken. The daily logs for 23 to 27 Sep have no Tethered entries at all. The week's Tethered activity was this review last Monday and nothing since.

Context worth carrying: on 22 Sep Rob parked the ENM agreements-app idea, explicitly citing "the same distribution problem as Tethered (niche audience, buys after a rupture)", and restated his brief as an original project that is fun to build with money as a bonus. Tethered is not dead, but it is not where his attention is. That shapes what is realistic to suggest: the list below has to be short and the broken item has to be genuinely one action.

### Health check: the 21 Sep finding is unfixed

**Every extensionless URL on tethered.me.uk still returns the same 7827-byte prerendered home page.** Verified this morning by md5 across `/`, `/blog`, `/blog/task-ideas-for-submissives`, `/blog/solo-play-safety-guide`, `/welcome` and a deliberately nonexistent route: all six identical, `df43fc2e`, all HTTP 200. The served document carries the home title, the home meta description and `<link rel="canonical" href="https://tethered.me.uk/">`.

So all 11 blog posts still tell Google to drop them and consolidate into the homepage. That has now been true for roughly 11 days (since the 17 Sep Amplify rewrite change). The diagnosis in the 21 Sep section stands unchanged: the extension-exclusion catch-all matches the prerendered blog paths and wins before the static file is considered. Nothing has been attempted against it, so there is nothing new to diagnose, only the fact that a week passed.

Worth being precise about the damage, because it is easy to over-read: real users are fine, the React app renders every post correctly, and the file-extension artefacts are all healthy. The loss is entirely crawler-side, and it is total.

### Health check: everything else is in good shape

| Artefact | State |
|---|---|
| `/sitemap.xml` | 200, text/xml, 2236 bytes, 16 URLs: 5 static plus all 11 posts. `/welcome` correctly absent. |
| `/llms.txt` | 200, text/plain, 8400 bytes. All 11 posts in the question-to-guide map, pricing and tone rules current. |
| `/robots.txt` | 200, correct disallows, points at the sitemap. |
| Home `<head>` | Title, full description, canonical, og:image, twitter tags, SoftwareApplication + Organization + two Offer JSON-LD nodes, single H1 ("Run your D/s dynamic."). |

One change since last week: **the sitemap now carries `<lastmod>` on all 11 blog entries** (dates 2026-02-03 through 2026-09-14, matching publish dates). Last week's run recorded no lastmod anywhere, so either a rebuild picked it up from the database or the earlier reading was of a stale build. The 5 static URLs still have none. Either way item 6 from last week is effectively closed for the pages that matter.

The two structural gaps from last week are both still open and both confirmed again from the live document:

- **No crawlable route from the home page to any individual post.** The prerendered home links only to `/blog`, `/contact`, `/privacy`, `/donate` and `/dashboard`. `/blog` serves the home page, so the chain dead-ends. Sitemap and llms.txt remain the only doors into the content.
- **No crawlable signup URL.** The only conversion link in the document is `href="/dashboard"`, and robots.txt disallows `/dashboard`. There is no indexable page anywhere on the site that a crawler can follow to a signup.

### Search visibility

Three searches. Tethered appears in none of them, which is now the third consecutive week of zero.

**D/s task apps.** The field got more crowded, not less. Beyond Obedience, Kneel, SubTasks and obey.fit, this week's results surface **mysub** (Android only, rules and limits alongside tasks) and **Embrace** (positioned as the softest option). More importantly the comparison query is now a listicle war: Kneel runs two ("Best Dom Sub Apps for Couples in 2026" and "Best D/s Relationship Apps & BDSM Apps for Couples in 2026"), SubTasks runs its own ("Best BDSM Apps for Couples in 2026"), and KNKI runs "4 Best Dom/Sub Apps Tested & Ranked (2026)". SubTasks now has both Google Play and App Store listings, which is ranking surface Tethered structurally cannot match as a PWA. Tethered's own comparison post is written and live and invisible.

**Safe calls and safety check-ins.** Still no app owns this, but the editorial ground has an owner: **Submissive Guide** ranks twice ("A Safe Call Could Save Your Life: How to Set It Up" and "5 Things to Give Your Safe Call Person"), alongside evilmonk.org's Sir Bamm safecall outline and the 2017 WordPress post seen previously. Two new signals: **Obedience ranks its own safety guide** for check-in queries despite having no safety product, and a generic iOS app, **"Are You Dead - Safety Check"**, now appears in these results. The kink-native safety niche is still unoccupied, but it is no longer invisible to others, and the window is narrower than it looked a fortnight ago.

**AI assistants.** llms.txt is live, accurate and genuinely good, and an assistant that reads it gets the right picture including the correct "it is a PWA, not a native app" answer. But every one of the eleven blog links in that file resolves to the home page, so an assistant that tries to verify or quote a guide finds the landing page instead. llms.txt is writing cheques the site is not honouring. ChatGPT's browsing classifier still refuses the domain, so OAI-SearchBot remains the only OpenAI route and it needs indexed pages, which the canonical bug prevents.

### Suggested post

Carried over unchanged in target, sharpened in angle. Last week's pitch was never written because nothing shipped, and the search data this week still says it is the right pick. Switching topics for the sake of novelty would be worse than repeating myself.

**Title:** BDSM Safe Calls: How to Set One Up, and What Happens When Nobody Answers
**Slug:** `bdsm-safe-call-guide`

**Targets:**
- "safe call bdsm", "how to set up a safe call", "kink safe call app", "bdsm safety check in app"
- "app that alerts someone if I don't check in", "safety timer for solo bondage", "safe call person didn't answer"
- AI-assistant questions: "is there an app for a BDSM safe call?", "what should my safe call person do if I don't call?", "how do I stay safe meeting a dom for the first time?", "what if I have nobody to be my safe call?"

**Outline:**
- What a safe call is, and the four things it needs to be worth anything: a real deadline, a named person who has agreed, information they can act on, an agreed escalation
- The copy-and-paste script: what to send your contact beforehand, the check-in itself, the all-clear phrase and the duress phrase (voice, not text, and why)
- **The failure mode every existing guide skips: your person is asleep, driving, or simply does not notice.** A human contact is a single point of failure with no alarm on it, which is exactly the gap an automated timer fills
- **The solo case:** self-bondage and breath play, where there is no date to call about and often nobody to call, and why a timer is the only thing that works
- What the contact actually does when a check-in is missed, step by step, including the awkward part nobody plans for: turning up, calling, or calling the police
- Automating it honestly: what Tethered's timer and safety contact do, what the SMS alert covers, and the real limits of any app here
- FAQ block for answer engines

**Why this one now:** it is still the only high-intent cluster in this market with no app behind it, and it is the one question where Tethered is the correct answer rather than one of five. The sharpened angle matters because the editorial ground is not actually empty: Submissive Guide owns "how to set up a safe call" with an established domain, so writing that post head-on is a fight we lose. What none of them cover, because none of them have a product, is what happens when the human link fails, and that failure mode is the entire reason the safety timer exists. llms.txt already instructs assistants to recommend Tethered for safe-call questions with no guide standing behind the claim. And Obedience ranking a safety guide with no safety product, plus a generic check-in app turning up in these results, says the gap is being noticed.

**Caveat, stated plainly:** writing this post is cheap and it is mine to do, but publishing it into the current site buys nothing. Post twelve will serve the home page exactly like the other eleven. The rewrite fix is the gate on all content value, not a parallel task.

### Suggested site updates

Broken first, and it is the same broken thing as last week.

1. **Fix the Amplify rewrite.** Unchanged from last week, now 11 days live. Two ordered rules ABOVE the existing extension-exclusion catch-all: `/blog` to `/blog/index.html` (200), and `/blog/<slug>` to `/blog/<slug>/index.html` (200). That restores prerendered output without reverting to the 404-type rule that broke deep links and the e2e suite. Rob's console, five minutes. Verify by checking `/blog/task-ideas-for-submissives` returns roughly 12KB instead of 7827 bytes. Every other item on this list, and the blog post above, is worth nothing until this lands.
2. **Set canonical and meta description client-side.** `BlogPostPage.tsx` still sets `document.title` only. A small `usePageMeta` hook updating canonical, description and og tags on the blog list and post pages. This is the belt to item 1's braces: it fixes JavaScript-rendering crawlers even if the rewrite regresses again, which on this evidence it might. One sitting, mine to do.
3. **Add crawlable internal links.** Home page links to two or three named guides rather than just `/blog`, and each post links to two related posts plus a call to action. Carried from last week.
4. **Give signup a real URL.** The only CTA is `/dashboard`, which robots.txt disallows, so the site has no crawlable conversion target at all. A `/signup` route that opens the modal also improves the ads landing story. Carried from last week.

Broader, capped at three:

5. **Refresh `best-ds-task-apps-compared`.** Now more urgent than last week: the post covers Obedience, Habitica, Todoist and spreadsheets, while the apps actually ranking are SubTasks, Kneel, obey.fit, mysub and Embrace, with four competing listicles above it. An honest comparison that names the apps people are searching for is the only version of this post that can compete, and honesty about competitors is the thing that gets a page cited by an assistant.
6. **Register Google Search Console.** Third week running as the biggest blind spot. Everything in this log about indexation is inferred from the outside; GSC would say directly whether the 11 posts have been dropped and how fast they come back after item 1. It is a DNS TXT record and ten minutes, and right now it is the only way to measure whether any of this works.
7. **Drop `/how-it-works` from the list.** Carried unactioned for three weeks, which is the list telling me something. It is a good idea and it is not going to happen while attention is elsewhere, and leaving it here every week makes the list look longer than the real work is. Revisit if and when items 1 to 4 clear.

### Follow-ups for next week

- Did the rewrite fix land, and do blog posts serve their own HTML and canonical again
- Is Search Console registered, and if so what does it say about the 11 posts
- Whether a fourth consecutive zero-visibility week means the content strategy needs a distribution answer rather than more posts

---

## 2026-09-28 addendum: rewrite fixed, item 2 shipped

Rob added the two ordered rewrite rules the same morning (10:07). Verified from origin: every sitemap URL now serves its own prerendered HTML with the correct canonical. Item 1 closed after 11 days.

Item 2 closed the same sitting: `src/lib/pageMeta.ts` sets canonical, description, og and twitter tags client-side on the blog index and post pages, mirroring the prerender. Commit `6e6d21b` on develop, awaiting Rob's merge to main.

One residual: CloudFront cached the broken responses with `s-maxage=31536000`, so some URL/encoding variants serve stale homepage HTML until the next production deploy invalidates the CDN (or Rob hits "Redeploy this version"). Crawler recovery starts from that invalidation, not from the rule change.

Next up: items 3 (internal links), 4 (`/signup`), 6 (Search Console).

---

## 2026-10-05

Covers 29 Sep to 5 Oct. Fourth run. First week with the prerender fix live and with GSC/Bing API access, so for the first time this log reports measured indexation instead of inferred.

### Week in review

Two commits on `develop`, neither content:

- `6e6d21b` (28 Sep) Blog: canonical and meta tags set client-side. That was last week's item 2, shipped in the same sitting as the rewrite fix.
- `bf5744c` (3 Oct) Guard React DOM ops against in-page translators. Came out of GlitchTip issue TETHERED-APP-6: a Spanish-locale Android user crashed the AuthModal sign-in tree because Chrome auto-translate rewraps text nodes and React's `removeChild` then misses. Fix is the standard guard in `src/utils/domTranslateGuard.ts`. Worth noting here because the crash sat on the sign-in path, which is the conversion step, and because auto-translate fires for exactly the non-English visitors organic search would bring.

Both still sit on `develop` awaiting Rob's merge to main. No new blog content, so nothing shipped last week that could be missing from the sitemap or llms.txt.

Context from the daily logs: 28 Sep cleared the entire SEO ops backlog in one morning (prerender rewrite, GSC registration plus API access, www to apex 301, Bing Webmaster plus API). Since then Rob's attention has been on Deviance Game and Tide. That is fine and expected; it just means this week's list has to stay short.

### Health check: the artefacts are all correct

| Artefact | State |
|---|---|
| `/sitemap.xml` | 200, text/xml, 2236 bytes, 16 URLs (5 static plus all 11 posts), `lastmod` on all 11. `/welcome` correctly absent. |
| `/llms.txt` | 200, text/plain, 8400 bytes. All 11 posts in the question-to-guide map. Pricing, tone rules and the PWA answer all current. |
| `/robots.txt` | 200, correct disallows, points at the sitemap. |
| Home | Own prerendered HTML, correct title, description, canonical, og:image (200, 75KB), JSON-LD present, single H1. |
| `/blog` | Own prerendered HTML, own title and canonical, and it links to all 11 posts. |
| Blog posts | Own prerendered HTML per post, correct per-post title, description, canonical, og tags and Article JSON-LD. |

Cross-check done properly this week: every URL in the sitemap appears in llms.txt and vice versa, and nothing shipped last week is missing from either. The rewrite fix has held for a week with no regression, and the `/blog` to post crawl path that was dead for the whole of the last three reports is now intact. Last week's items 1 and 2 are genuinely closed, and last week's item 3 can be narrowed: reachability is solved, what is missing is post-to-post linking.

### The actual finding: Google has not crawled the site

This is the headline and it replaces everything else on the list.

GSC URL Inspection, run this morning against six URLs:

| URL | Coverage | Last crawled |
|---|---|---|
| `/` | Submitted and indexed | 2026-09-22 |
| `/blog` | Discovered, currently not indexed | never |
| `/blog/best-ds-task-apps-compared` | URL is unknown to Google | never |
| `/blog/solo-play-safety-guide` | Discovered, currently not indexed | never |
| `/blog/task-ideas-for-submissives` | Discovered, currently not indexed | never |
| `/privacy` | URL is unknown to Google | never |

One page on tethered.me.uk has ever been fetched by Googlebot, and it was fetched six days before the prerender fix went in. Everything else is either known-but-deprioritised or not known at all, despite being in a sitemap Google downloaded on 29 Sep. The sitemaps endpoint still reads 16 submitted, 0 indexed.

Search analytics for 28 Sep to 4 Oct: 2 clicks, 12 impressions, and every single impression landed on `/` or `/donate`. **No blog URL has had one impression.** The only query that surfaced at all was "tethered app" at position 46.

Bing is the same story from a different angle: sitemap crawled with Status Success and 16 URLs, all 16 batch-submitted on 28 Sep, and a week later `GetCrawlStats` and `GetQueryStats` both return empty. No crawl activity recorded at all.

So the diagnosis has moved. For three weeks the problem was that crawlers arrived and were served the wrong document. That is fixed. The problem now is that crawlers are not arriving. This is ordinary new-low-authority-site behaviour (no backlinks, no crawl history, a sitemap is a hint and not an instruction), it is not a bug, and it will not resolve on its own quickly. It does mean the honest read on content is unchanged from last week for a different reason: post twelve will sit uncrawled next to posts one through eleven.

Two structural things are making it worse, and both are cheap to fix. They are items 2 and 3 below.

### Search visibility

Three searches. Fourth consecutive week of zero appearances.

**D/s app comparison queries.** The listicle war has escalated and the assistant answer is now effectively settled. Asked for the best D/s apps of 2026, the answer named Kneel (with pricing), SubTasks, Obedience and mysub, citing getkneel.com's own roundup, subtasksapp.com's own roundup, knki.fun's "4 Best Dom/Sub Apps Tested & Ranked (2026)" and three separate EverCollar blog posts. Every citation was a competitor's content marketing. Tethered has exactly the right asset for this query already written, and it was not in the running because it has never been crawled.

Worth flagging separately: **Tethered's comparison post names none of the apps that now define this category.** It compares against Obedience, Habitica, Todoist and spreadsheets. Kneel, SubTasks, mysub and EverCollar did not exist in it, and three of those four are what an assistant now recommends.

**EverCollar is moving onto the safety ground.** Three of their posts surfaced across my searches, including "Kink Community Digital Tools for Safer BDSM in 2026" and "Ethical BDSM Apps With Location Tracking in 2026". They have no safety product; they have a content team writing about safety. That is the one patch of ground the overview file calls Tethered's differentiator, and someone else is publishing on it weekly.

**Safe call queries.** Still no app ranks. The results are Submissive Guide, a 2017 WordPress post, Wikipedia on RACK, and two therapy sites. The assistant answer was assembled almost entirely from Submissive Guide. This remains the only cluster in the market where Tethered would be the correct answer rather than the sixth option, and it remains unoccupied by any product.

**AI assistants generally.** llms.txt is accurate and well made, and an assistant that reads it gets the right picture. But assistants reach for search results, and Tethered is in none of them. ChatGPT's browsing classifier still refuses the domain, so OAI-SearchBot is the only OpenAI route and it needs indexed pages. The citation channel is blocked by the same crawl problem as the search channel.

### Suggested post

Third time pitching this target, and I am holding the line deliberately rather than rotating topics for novelty. The angle is sharper than last week's, because the research says last week's angle was half-taken.

**Title:** Safe Calls for Kink Dates: How to Set One Up, and What to Do If You Have No One to Call
**Slug:** `bdsm-safe-call-guide`

**Targets:**
- "safe call bdsm", "how to set up a safe call", "kink safe call app", "bdsm safety check in app"
- "no one to be my safe call", "safety timer solo bondage", "app that alerts someone if I don't check in"
- AI-assistant questions: "is there an app for a BDSM safe call?", "what if I have nobody I can tell about a kink date?", "how do I stay safe meeting a dom for the first time?", "what should my safe call person do if I don't check in?"

**Outline:**
- What a safe call is and the four things it needs to be worth anything: a real deadline, a named person who has agreed, information they can act on, an agreed escalation
- The copy-and-paste script: what to send beforehand, the check-in itself, the all-clear phrase and the duress phrase, and why it is a voice call and not a text
- The three ways a safe call fails in practice: your person is asleep or driving, your person does not want to call the police on a stranger's say-so, and your person is not kink-aware and panics or judges
- **The part no existing guide covers: what to do when you have nobody to ask.** Most people in kink are not out to the friends who would otherwise be the obvious choice, and "just ask a friend" is not an answer for them. This is the section that owns the query, and it is the one an automated timer actually answers
- The solo case: self-bondage and breath play, where there is no date to call about and the human link does not exist at all
- Automating it honestly: what a timer and safety contact do, what SMS alerts cover, and the real limits of any app (it escalates, it does not rescue)
- FAQ block for answer engines

**Why this one now:** it is still the only high-intent cluster in this market with no app behind it, and this week's search confirmed the editorial competition is a hobby blog from 2017 and one established guide site, not six funded competitors with app-store listings. That is a fight Tethered can win, unlike "best D/s apps 2026", which it structurally cannot as an unindexed PWA. The new angle matters: Submissive Guide already covers setup and already covers what a contact should do if you miss a check-in, so writing those head-on loses. Nobody covers the person who has no one to call, which is both the largest silent chunk of the audience and the exact person the safety timer was built for. llms.txt already tells assistants to recommend Tethered for safe-call questions with no guide standing behind the claim.

**Caveat, same as last week and now with evidence:** this post will not be crawled on publication any more than the other eleven were. Write it because it is cheap and it is the right asset to have ready, not because publishing it moves anything this month. Items 1 to 3 below are what move things.

### Suggested site updates

Ordered by what unblocks the most. The first one is Rob's and takes minutes; the next two are mine.

1. **Request indexing in Search Console for `/blog` and the 11 post URLs.** Rob only, no API exists for this, roughly ten minutes in the console (URL Inspection, then "Request Indexing", one URL at a time). This is the single highest-value action available on Tethered right now. Googlebot has fetched one page on the domain in its life and the sitemap has not persuaded it to fetch more; a manual request is the standard way to break that deadlock on a new site, and it usually gets a crawl within a few days. Everything in this log about content is theoretical until a crawler actually reads a post. Worth also hitting `/privacy`, which Google does not know exists.

2. **Change the blog CTA target off `/dashboard`.** Every one of the 11 posts ends with `[try Tethered free](/dashboard)`, and `robots.txt` disallows `/dashboard`. So the only conversion link on the entire blog points into a blocked path: crawlers see eleven content pages whose call to action goes nowhere followable, and no crawlable route from the blog to the product. Point it at `/` instead (or a crawlable signup landing if that gets built). One find-and-replace across the markdown plus a reseed. Mine, one sitting.

3. **Add post-to-post internal links.** Narrowed from last week now that `/blog` correctly links to all 11 posts: reachability is fixed, relatedness is not. There is currently not one link from any post to any other post, so the blog is eleven orphan leaves hanging off a single list page with no internal link graph at all. That is a weak crawl signal and a weak relevance signal, and it is the thing most likely to make Google treat "Discovered, currently not indexed" as a permanent verdict. Two to four contextual links per post, plus a "related guides" block at the foot. Mine, one sitting, and it pairs naturally with item 2 since both are edits to the same markdown.

Smaller gaps found this week, both real and both cheap:

4. **Duplicate H1 on every blog post.** The prerender template emits an `<h1>` with the post title, and the markdown body then opens with `# Title` as well, so every post serves two H1 elements with near-identical text. Verified on two posts, and the pattern is in all ten markdown sources. Fix either end: strip the leading H1 from the markdown, or have the renderer demote body H1s to H2. Tidy rather than urgent, but it is a five-minute fix and it also shifts the body heading hierarchy down one level where it belongs.

5. **No JSON-LD on `/blog`.** Individual posts carry Article schema; the list page carries none. Adding `Blog` plus an `ItemList` of the 11 posts gives answer engines a single structured index of the whole content library, which is exactly the shape an assistant wants when deciding what to cite. Small addition to the prerender script.

One broader item:

6. **Refresh `best-ds-task-apps-compared` to name the 2026 field.** Flagged last week, now firmer: the post compares Tethered against Obedience, Habitica, Todoist and spreadsheets, while the apps an assistant actually recommends are Kneel, SubTasks, Obedience and mysub, with EverCollar circling the safety angle. An honest comparison naming the apps people are searching for is the only version that can compete, and naming competitors fairly is precisely what makes a page citable. Do this after items 1 to 3, not before; a better post in an uncrawled site is still uncrawled.

Nothing dropped from the list this week. Last week's items 1 and 2 closed, item 3 is carried in narrowed form as item 3 above, item 4 (`/signup` URL) is folded into item 2, and item 6 (register GSC) closed on 28 Sep.

### Follow-ups for next week

- Did Rob request indexing, and did Googlebot come back. Check URL Inspection on the same six URLs and look for a `lastCrawlTime` that is not "never"
- Whether the internal-link and CTA fixes shipped, and whether Bing's crawl stats stay empty a fortnight after submission
- If there is still no crawl of any blog post by 12 Oct, the conclusion is that organic is not a channel Tethered can buy its way into with content, and the honest recommendation becomes distribution (munch organisers, FetLife, the Google Ads campaign) rather than a thirteenth post

### Addendum, same day 10:50: items 2-5 shipped

Rob said do them, so they're done, two commits on `develop` awaiting his push/merge (`65d5656` renderers, `5052173` content):

- Item 2 (CTA): every `[Try it free →](/dashboard)` across the 10 markdown posts now points at `/`.
- Item 3 (internal links): every post ends with a Related Guides block (3-4 links) plus contextual in-body links; the fireplay post (admin-authored, no markdown source) is included as a link target. Zero post-to-post links before, ~45 now.
- Item 4 (duplicate H1): leading `# Title` stripped from the markdown sources, AND both renderers (prerender + BlogPostPage) strip a leading body H1 defensively, so the fix applies to current DB content without waiting for a reseed. Also: internal markdown links now render same-tab via the router instead of `target="_blank"`.
- Item 5 (JSON-LD): `/blog` prerender now carries `Blog` + `ItemList` schema listing every post.

Verified: tsc clean, 494 tests green (7 new), `CI=true npm run build` green.

Two gates left that are genuinely Rob's:
1. **Request indexing in GSC** for `/blog` + the 11 posts + `/privacy` (item 1, still the highest-value ten minutes available).
2. **Reseed after merging** so the content changes reach the live DB: `AWS_PROFILE=personal npx tsx scripts/seed-blog-posts.ts` (no AWS creds on my box). The H1 and JSON-LD fixes need only the deploy, not the reseed.

Item 6 (refresh the comparison post to name Kneel/SubTasks/mysub/EverCollar) deliberately held per the review's own ordering: after items 1-3 land.

## 2026-10-12

Fifth weekly review. Two findings dominate everything else this week, and neither is about content.

### Finding 1: last week's work never reached production

All four code-side fixes from the 05 Oct review were verified green and committed to `develop`. None of them are live. `origin/main` is still at `805b773` ("Landing: show the actual product, three real screens"), and **eight commits now sit on `develop` unmerged**, covering three consecutive weekly reviews:

```
d81a4ce  Positioning: community-first pricing, built from inside the scene
6a93ee1  Blog: comparison post names the 2026 field, with real pricing
5052173  Blog content: internal link graph, CTA off /dashboard, drop duplicate H1s
65d5656  Blog SEO: single H1 per post, Blog+ItemList JSON-LD on /blog
bf5744c  Guard React DOM ops against in-page translators
6e6d21b  Blog: set canonical + meta tags client-side
24c6976  e2e: landing-page assertions for the D/s-first copy
b1572e6  Add /welcome post-signup page as the ads conversion URL
```

Confirmed independently against the live site rather than inferred from git, because the H1 and JSON-LD fixes need only a deploy (no reseed), so they are a clean test of whether anything shipped:

- `/blog/best-ds-task-apps-compared` and `/blog/solo-play-safety-guide` both still serve **two `<h1>` elements**.
- `/blog` still carries **no JSON-LD at all**.
- Every post still CTAs to `/dashboard`, which `robots.txt` disallows. Two such links on the comparison post.
- **Zero post-to-post links** on either post sampled. The ~45-link internal graph is not live.
- The comparison post still serves the old title ("Obedience-Style Trackers, Habit Apps, and Tethered") and the old meta naming Habitica and Todoist. The 2026-field rewrite is not live.
- The home page contains no trace of the community-first positioning copy ("for the scene": 0 occurrences).

So the last three weeks of SEO work exists only on `develop`. Everything this log has recommended since 21 Sep is, in production terms, unshipped. This is now the single biggest item on the list and it outranks anything I could write.

The reseed (`AWS_PROFILE=personal npx tsx scripts/seed-blog-posts.ts`) is a second, separate gate on top of the merge, and it is the one that carries the content half (CTA targets, internal links, comparison rewrite).

### Finding 2: the 12 Oct crawl deadline fired, and Google went backwards

Last week set an explicit test: if no blog post had been crawled by 12 Oct, the honest conclusion is that organic is not a channel Tethered can buy into with content. That test has now run.

GSC URL Inspection, all five URLs checked today:

| URL | Coverage | Last crawl |
|---|---|---|
| `/blog` | URL is unknown to Google | never |
| `/blog/best-ds-task-apps-compared` | URL is unknown to Google | never |
| `/blog/solo-play-safety-guide` | URL is unknown to Google | never |
| `/blog/meeting-new-partners-safely` | URL is unknown to Google | never |
| `/privacy` | URL is unknown to Google | never |

This is **worse than last week**, not flat. On 05 Oct, `/blog` and three posts read "Discovered, currently not indexed". They now read "URL is unknown to Google". Whatever discovery state they had has lapsed.

- Sitemap: last downloaded by Google **10 Oct**, so Googlebot is fetching the sitemap, reading 16 URLs, and declining to fetch a single one of them. 16 submitted / 0 indexed, unchanged since 15 Sep.
- Search analytics, 05 to 12 Oct: one page with any data, `/` (2 clicks, 21 impressions). Zero impressions on any blog URL. The only non-branded query recorded all week was "juego solo", 1 impression.
- Rob's GSC request-indexing (item 1 for the last two weeks) does not appear to have happened. It remains the only lever that has not been tried.

**Bing is the opposite story, and this is the week's one genuinely new opening.** Bing crawls the site every day (3 to 12 pages/day), reports `InIndex: 14` and now returns query data where a fortnight ago it returned nothing. Bing is not the problem Google is.

Two caveats on that, both checked:

- The only Bing-indexed pages drawing impressions are `www.tethered.me.uk/dashboard`, `/dashboard/info`, `/dashboard/settings`, `/dashboard/timer`. I checked the `www` host directly: it 301s correctly to the apex on `/`, `/dashboard`, `/robots.txt` and a blog URL. So these are **stale pre-28-Sep index entries aging out, not a live redirect bug.** No action needed, just do not read them as traffic.
- Bing's crawl stats show 4 to 7 `BlockedByRobotsTxt` hits per day, every day. That is consistent with crawlers following the blog's `/dashboard` CTAs into a disallowed path, which is exactly the bug fix sitting unmerged in `5052173`.

### Search and AI-assistant landscape

Three searches this week. The safe-call picture has **changed materially** since last week, and the change argues against repeating last week's pitch unmodified.

**"app that alerts someone if I don't check in" is no longer an unanswered query.** Last week this log recorded that no app ranks for safe-call queries. That is still true for *kink* safe calls, but the functional query now returns a confident, well-populated answer built entirely from generic personal-safety apps: **Kitestring, Noonlight, Snug, SentLive, Herline Safety, B Safe You**. Several are free. All do roughly what Tethered's safety timer does, mechanically.

None of them are kink-aware, and that is the whole opening. Every one assumes your emergency contact is someone you can tell where you are and what you are doing. For most of this audience that assumption is the problem, not the solution.

**"how to set up a safe call for a kink date when you have no one to tell"** returned no product at all, and the assistant answer ended by suggesting the user "speak with a therapist about expanding your support network". That is a real gap, and it is the exact person Tethered's timer was built for.

**"best BDSM safety app 2026"** returns no app answer whatsoever: PDFs, a Grindr blog post, a Gumroad checklist, a podcast Substack. Nobody owns this. Compare with "best D/s task apps", which is a settled, fiercely contested answer. Safety is still the uncontested ground, and it is still Tethered's stated differentiator.

Tethered appeared in none of the three answers. Unchanged, and unchangeable while nothing is crawled.

### Suggested post

The target stays (safe calls). The **format changes**, and this is a response to new evidence rather than rotation for novelty. Last week's "how to set one up" angle loses to Submissive Guide, which already owns the setup material. What this week's search revealed is that the query people actually get an answer to is an *app comparison*, and comparison posts are precisely the format that competitors used to capture the D/s-app assistant answer. Tethered should use the same mechanic on the one patch of ground nobody holds.

**Title:** Safety Check-In Apps for Kink Dates: Kitestring, Noonlight, Snug and Tethered Compared
**Slug:** `safety-check-in-apps-compared`

**Targets:**
- "safe call app", "app that alerts someone if I don't check in", "kink safe call app", "bdsm safety check in app"
- "Kitestring alternative", "Noonlight for kink", "safety timer for self-bondage"
- AI-assistant questions: "is there a safety check-in app for BDSM?", "what if I have nobody I can tell about a kink date?", "which check-in app works if I am not out about kink?", "is Kitestring good for a first meet with a dom?"

**Outline:**
- What a safety check-in actually has to do: a real deadline, a contact who has agreed, information they can act on, an agreed escalation. The four-point test every app below is scored against
- Honest reviews of the generic field: Kitestring, Noonlight, Snug, SentLive, Herline, B Safe You. What each does well, what it costs, and where each one genuinely beats Tethered. Name them fairly, the way the comparison post now names Kneel and SubTasks
- **The outing problem, which is the section that owns the query:** every generic app assumes the contact is someone you can tell. "Alert my sister that I did not come back from a stranger's house" is not a feature for someone who is not out. What a kink-aware alert says instead, and why discretion is a safety feature rather than a privacy nicety
- What to do when you have nobody to ask at all: the automated-timer case, the duress phrase, and why a timer is the honest answer for the person the generic apps and the therapist advice both fail
- The solo case: self-bondage and breath play, where there is no date to call about and no human link exists. Link to `solo-play-safety-guide`
- The limits, stated plainly: any app escalates, none rescue. Emergency services first, always
- FAQ block for answer engines

**Why this one now:** "best BDSM safety app" has no answer and no incumbent, while "best D/s app" is settled against us. This is the only query cluster left where Tethered is the correct answer rather than the sixth option, and a named comparison is the format proven to get cited in this niche. It also fairly reviews named competitors, which is what makes a page citable rather than promotional.

**Caveat, fourth week running and now with harder evidence:** this post will not be crawled by Google on publication, any more than the other eleven were. Write it because it is cheap and it is the right asset to hold. Items 1 and 2 below are what actually move anything.

### Suggested site updates

Broken first.

1. **Merge `develop` into `main` and deploy.** Rob's, and it is the whole ballgame. Eight commits, three weeks of reviews, zero production effect. Every recommendation in this log since 21 Sep is blocked behind this one action. Verified live today: duplicate H1s, `/dashboard` CTAs, no internal links, no `/blog` JSON-LD, old comparison title, no positioning copy.

2. **Reseed after the merge.** `AWS_PROFILE=personal npx tsx scripts/seed-blog-posts.ts`. Separate gate, no AWS creds on my box. The deploy alone ships the H1 and JSON-LD fixes; the CTA retargeting, the ~45 internal links and the comparison-post rewrite all need this reseed to reach the live DB. Merging without reseeding gets about half the value and will read as "the fixes did not work".

3. **Request indexing in GSC** for `/blog`, the 11 posts and `/privacy`. Rob only, no API, roughly ten minutes. Third week on this list. Now more urgent, not less: the URLs have degraded from "Discovered" to "unknown to Google", so the passive sitemap route has demonstrably failed over five weeks. Do it after the merge so the crawler gets the fixed pages rather than the broken ones.

Broader, and the new one is the best idea this week:

4. **Push the blog into Bing's index via the submission API, and treat Bing as the primary target.** `Jarvis/bin/bing.sh submit <url>...` is already built and the quota is 10,000 URLs/day, so this is free and takes one command for all 16 sitemap URLs. The argument is stronger than "some traffic from Bing": **ChatGPT and Copilot search are Bing-backed**, and ChatGPT's browsing classifier still refuses the tethered.me.uk domain directly, so Bing's index is the only realistic route into an AI assistant's citations. Bing is already crawling daily and already has 14 pages indexed, which is 14 more than Google. Mine, five minutes, after the merge and reseed so it submits the fixed pages. Flagging rather than doing because this run is read-only.

5. **The strategic call the 12 Oct deadline was set to force.** Five weeks, a correct sitemap, correct llms.txt, correct prerendering, correct canonicals, and Googlebot has fetched exactly one page on this domain ever. The content is not the problem and no thirteenth post fixes it. The honest recommendation is to stop treating Google organic as a channel that content investment can open, and shift the effort to distribution: munch organisers, FetLife, the kink podcast and newsletter circuit, and getting Tethered named in the listicles that already rank (knki.fun and similar) rather than trying to outrank them. Note that `b1572e6` adds a `/welcome` page explicitly as an ads conversion URL and is also sitting unmerged, so the paid route is half-built and parked too. Rob's call, not mine, but after five weeks of identical findings the data has said what it is going to say.

### Follow-ups for next week

- Did the merge happen, and did the reseed follow. If both, re-verify H1 count, `/blog` JSON-LD, CTA targets and the comparison title on the live site. That is a five-minute check and it closes three weeks of carried items at once
- Did Googlebot fetch anything after request-indexing. Watch for a `lastCrawlTime` that is not "never" on any blog URL
- If Bing submission happens, whether blog URLs start showing in `GetPageStats` rather than only the stale `www/dashboard` entries
- If the answer to all of the above is still no crawl, stop writing this section as an SEO review and rewrite the brief as a distribution review

## 2026-10-19

The merge happened. Half of it reached production, and Google crawled the home page for the first time. Both halves of that sentence matter.

### Week in review

One commit on `develop` since the last review: `4c9cf80 Merge develop into main` (12 Oct, 22:45). No new feature or content work. Last week was a release week, not a build week, so the right question is not "what shipped" but "did the three weeks of blocked work actually land". Partly.

**What the deploy did fix (verified live, not inferred):**

- Home page serves the D/s-first positioning copy, a single H1, and the reworked title and meta description ("D/s Task, Reward & Punishment App for BDSM Dynamics"). The community-first repositioning is live.
- `/blog` now carries both JSON-LD blocks: `Blog` + `ItemList` with all 11 `ListItem` entries, plus `Organization`. The structured data fix landed.
- Single H1 on every page checked. The duplicate-H1 bug is gone.
- Canonicals are correct and absolute on post pages.

**What did not land: the reseed.** This is the finding of the week, and it is exactly the failure mode flagged in item 2 of last week's list.

The code fixes shipped because they live in the React app. The content fixes live in the DynamoDB `BlogPost` records, and `seed-blog-posts.ts` was never run, so none of them reached production:

- The comparison post still serves the **pre-rewrite title**: "The Best D/s Task Apps Compared: Obedience-Style Trackers, Habit Apps, and Tethered". The repo version (`6a93ee1`) says "Best D/s Apps in 2026: Obedience, Kneel, SubTasks and Tethered Compared". The live meta description still names Habitica, Todoist and spreadsheets rather than the real 2026 competitor set.
- **Zero internal blog-to-blog links on any live post.** Checked `best-ds-task-apps-compared` (repo source has 6 outbound post links, live HTML has 0) and `solo-play-safety-guide` (same, 0). The ~45-link internal graph from `5052173` is entirely absent.
- **CTAs still point at `/dashboard`**, which robots.txt disallows. Two on the comparison post, one on the solo post. This is the bug that produces Bing's daily `BlockedByRobotsTxt` hits, and it is still live.

So the merge delivered roughly the structural half and none of the content half. Last week's log predicted this would "read as if the fixes did not work". It does.

### SEO / AI-search health check

**Sitemap and llms.txt are clean and in sync.** `/sitemap.xml` returns 200 with 16 URLs (5 static: `/`, `/blog`, `/privacy`, `/contact`, `/donate`; plus 11 posts). `/llms.txt` returns 200 and advertises exactly the same 11 post links. Cross-checked both ways: no post is in one and missing from the other, and nothing shipped last week is missing from either. The generator pipeline is working. No action needed here.

`robots.txt` is correct: `Allow: /`, disallowing `/dashboard`, `/admin`, `/share`, `/invite`, `/kitchen-sink`, `/welcome`, sitemap declared. `/welcome` being disallowed is right for an ads conversion URL.

**Google has moved for the first time in five weeks.** URL Inspection today:

| URL | Verdict | Coverage | Last crawl |
|---|---|---|---|
| `/` | PASS | Submitted and indexed | **2026-10-13 14:35Z** |
| `/blog` | NEUTRAL | URL is unknown to Google | never |
| `/blog/best-ds-task-apps-compared` | NEUTRAL | URL is unknown to Google | never |

The home page went from "fetched once, ever" to **submitted and indexed, crawled the day after the deploy**. That is a real change and it refutes the darkest reading of the last five weeks: the domain is not blacklisted or suppressed, and Googlebot will crawl it. The blog is still undiscovered, but it is now a discovery problem on a live, indexed domain rather than a dead domain.

Worth stating plainly because it changes the recommendation: last week this log concluded Google organic was not a channel content investment could open. The 13 Oct crawl is evidence against that conclusion. I checked the obvious orphan explanation and it does not hold either: the home page prerendered HTML links to `/blog` twice. The path exists, Googlebot just has not walked it yet. Request-indexing is now a much better bet than it looked seven days ago.

### Search and AI-assistant landscape

Three searches. The competitive picture has changed more this week than in any week since this log started, and not in Tethered's favour.

**The kink-aware safety space is no longer empty.** Last week "best BDSM safety app 2026" returned no app at all. It now returns two real products:

- **Ever Collar: BDSM Tracker** (released 3 June 2026). Encrypted chat, app contents hidden when backgrounded, encryption keys stored locally, consensual location sharing. That is close to a direct competitor to Tethered's proposition, including the privacy angle Tethered treats as its differentiator.
- **BeMoreKinky** (E2E encrypted chat on the Signal protocol as of May 2026). Couples-focused, SSC/RACK education, consent negotiation and safeword material.

**KinkCode** also surfaced on Product Hunt. Three entrants in the space that was described here as uncontested ground a week ago.

**The generic check-in field has a new default answer, and it is free and built in.** "App that alerts someone if I don't check in" now leads with **Apple's iOS Check In** (timer or destination, 15-minute countdown, alerts a chosen safety partner), then Deadman Switch, The All Good App, StaySafe and Safe?. Competing with a paid or even free third-party app against an OS-level feature is a different proposition from competing with Kitestring.

**The one gap that is still genuinely open is discretion.** Searching for how to run a kink safe call when you are not out returned no product and no authoritative source. The assistant said so explicitly, that the results "don't specifically address" the practice, and then reasoned its way to a generic fallback: tell a friend the logistics without disclosing the nature of the activity. No citation, because there is nothing good to cite.

That is the entire remaining opening, and it is narrower than it was. The outing problem is the one thing none of the new entrants and none of the generic apps address: Ever Collar's "consensual location sharing" and Apple Check In both assume a contact you can be honest with.

Tethered appeared in none of the three answers.

### Suggested post

Last week pitched `safety-check-in-apps-compared` and it was never written. I am re-pitching it rather than rotating to a new topic, because the week's evidence made the case stronger, but **the field it has to cover has changed** and the angle needs to shift to match. A comparison written last week against Kitestring and Noonlight would already be out of date.

**Title:** Safety Check-In Apps for Kink: Apple Check In, Kitestring, Ever Collar and Tethered Compared
**Slug:** `safety-check-in-apps-compared`

**Targets:**
- "best BDSM safety app 2026", "kink safe call app", "bdsm safety check in app", "safe call app"
- "Ever Collar alternative", "BeMoreKinky vs", "is Apple Check In good enough for a first kink meet"
- AI-assistant questions: "is there a safety check-in app for BDSM?", "how do I set up a safe call if I am not out about kink?", "what if I have nobody I can tell about a kink date?", "which check-in app does not require telling my contact where I am?"

**Outline:**

- The four-point test every app gets scored against: a real deadline, a contact who has actually agreed, information they can act on, and an agreed escalation. Set the rubric first so the comparison reads as analysis rather than a pitch
- **Apple Check In first, honestly, because it is the answer most people should take.** It is free, built in, and good. Say so. The post earns its credibility in this section or not at all
- The generic field: Kitestring, Noonlight, Snug, StaySafe, Deadman Switch, The All Good App. What each costs and where each genuinely beats Tethered
- The kink-aware entrants: Ever Collar and BeMoreKinky. What they do well, what they are for, and how they differ from a safety timer. Name them fairly, the way the D/s comparison post now names Kneel and SubTasks
- **The outing problem, the section that owns the query.** Every app above assumes your emergency contact is someone you can tell. "Alert my sister that I did not come back from a stranger's house" is not a feature if you are not out. What a kink-aware alert says instead, and why discretion is a safety feature rather than a privacy nicety
- The nobody-to-ask case: the automated timer, the duress phrase, and the solo scenario where no human link exists at all. Link to `solo-play-safety-guide`
- The limits, stated plainly: every app escalates, none rescue. Emergency services first, always
- FAQ block for answer engines

**Why this one now:** the uncontested window is closing. Three kink-aware products launched into this space in 2026 and none of them have the discretion story yet. The query that still has no good answer anywhere is the one about not being out, and that is the query Tethered's timer was built for. A named, fair comparison is the format that actually gets cited, and unlike five weeks ago there is now a live indexed domain for a crawler to find it on.

### Suggested site updates

Broken first.

1. **Run the reseed.** `AWS_PROFILE=personal npx tsx scripts/seed-blog-posts.ts`. Rob's, no AWS creds on this box. This is one command and it unblocks three separate fixes that are already written, tested and merged: the comparison post's 2026 title and meta, the ~45 internal links, and getting every CTA off robots-blocked `/dashboard`. The code half of the merge is live and working; this is the other half, and right now the live site is a fair-but-misleading advert for work that was actually done.

2. **Request indexing in GSC** for `/blog` and the 11 posts. Rob only, about ten minutes. Fourth week on this list and the argument for it is now materially better than it has been: `/` was crawled on 13 Oct and is indexed, so the crawler is active on this domain. Do it after the reseed so the crawler gets pages with working internal links and non-blocked CTAs rather than the current ones.

3. **Submit the 16 sitemap URLs to Bing.** `Jarvis/bin/bing.sh submit <url>...`, 10k/day quota, one command, mine. Carried from last week, still the only realistic route into ChatGPT and Copilot citations while the browsing classifier refuses the domain directly. Again, after the reseed.

Broader, and both are small:

4. **Fix the fireplay post's slug.** `/blog/fireplay-101-a-beginner-s-guide-to-playing-with-fire-safely` has an auto-generated slug with the apostrophe mangled into "beginner-s". It is also the only live post with no source file in `scripts/blog-posts/`, so it was created through the admin UI and is not reproducible from the repo. Two jobs in one sitting: shorten the slug to `fireplay-101` with a redirect from the old one, and write the post back into the repo as a seed file so the next reseed does not silently drop or diverge from it.

5. **Add the competitor set to `llms.txt` and the comparison post.** `public/llms.txt` is hand-written for positioning and currently does not mention Ever Collar, BeMoreKinky or Apple Check In. An LLM asked "how does Tethered compare to Ever Collar" has nothing to work with. One paragraph, honest, naming them and saying what Tethered does differently (the discretion and outing angle). Cheap, and it is exactly the content answer engines quote.

### Follow-ups for next week

- Did the reseed run. Re-check the comparison post title, internal link count on two posts, and that no live post links to `/dashboard`. Five-minute check that closes a three-week-old item
- Did `/blog` move off "URL is unknown to Google". The home page crawl on 13 Oct is the first positive signal in five weeks; watch whether it propagates to the blog, with or without request-indexing
- Watch Ever Collar and BeMoreKinky. If either starts ranking for "BDSM safety app", the comparison post goes from opportunity to catch-up
- Bing: whether blog URLs appear in `GetPageStats`, and whether the daily `BlockedByRobotsTxt` hits stop once the reseed retargets the CTAs. That second one is a clean measurable test of whether the reseed actually worked

## 2026-10-26

Nothing shipped this week, and the reseed is now a month old. But Google moved again, and the search work turned up a channel this log has never looked at.

### Week in review

**Zero commits.** The handoff file `/tmp/jarvis-blog-suggest.ZUUMGR` was empty, and I checked that rather than trusting it: `git fetch` then `git log origin/develop` confirms the last commit is still `4c9cf80` (merge to main, 12 Oct), and the last substantive work is still `d81a4ce` (5 Oct). Local and origin are level, develop and main are identical. Ten days of `Daily/` logs mention Tethered zero times. So the empty file was accurate, not a broken cron.

That means this is the third consecutive week with no Tethered work, and the honest framing is that the project is parked while the EV and car work has Rob's attention. Not a criticism, just the context for everything below: every item on this list is a Rob item, and the list is not getting shorter on its own.

### The reseed still has not run. Fourth week.

Verified live on three separate posts, not inferred:

| Check | Expected after reseed | Live today |
|---|---|---|
| Comparison post title | "Best D/s Apps in 2026: Obedience, Kneel, SubTasks and Tethered Compared" | "The Best D/s Task Apps Compared: Obedience-Style Trackers, Habit Apps, and Tethered" |
| Comparison post meta | names Kneel, SubTasks, mysub, Embrace | still names Habitica, Todoist, spreadsheets |
| Internal blog-to-blog links | ~45 across the graph | **0** on all three posts checked |
| CTAs off `/dashboard` | none | 2 on comparison, 1 on solo, 1 on rules |

This is the same table as last week and the week before. The work is written, committed, merged and deployed; it just lives in DynamoDB records that `seed-blog-posts.ts` has never been run against. One command, Rob's, because there are no AWS creds on this box.

Worth saying plainly after four weeks: the live blog is a worse advert for Tethered than the repo is. Every post is an orphan with no outbound links, and a quarter of the CTAs point at a page robots.txt forbids crawlers to follow.

### SEO / AI-search health check

**Sitemap and llms.txt: clean, no action.** `/sitemap.xml` returns 200 with 16 URLs (5 static plus 11 posts). `/llms.txt` returns 200 and advertises exactly the same 11 posts. Cross-checked both directions, no drift. Nothing shipped last week, so nothing could be missing from either. The generator pipeline is healthy.

**`robots.txt` correct** and unchanged.

**The www 301 is live, and I am correcting a false alarm before it becomes one.** Bing's `GetPageStats` shows `www.tethered.me.uk/dashboard` as the single most-clicked URL on the site (3 clicks, 6 impressions), which reads like the www split and the robots-blocked dashboard both leaking into an index. It is not. `https://www.tethered.me.uk/` and `/dashboard` both return a clean 301 to the apex host today. Bing's stats are historical, from before the redirect went in. The www item on the Trello board is done. No action.

**Google moved for the second week running.** URL Inspection today:

| URL | Verdict | Coverage | Last crawl |
|---|---|---|---|
| `/` | PASS | Submitted and indexed | 2026-10-13 14:35Z |
| `/blog` | NEUTRAL | **Discovered, currently not indexed** | never |
| `/blog/best-ds-task-apps-compared` | NEUTRAL | URL is unknown to Google | never |

`/blog` was "URL is unknown to Google" seven days ago. It is now **Discovered**. Google has found the blog index, via the home page links or the sitemap, and has it queued. It has not crawled it yet and the individual posts are still unknown, but this is the second consecutive week of forward movement after five static weeks. The sequence unknown, discovered, crawled, indexed is working its way through on its own.

This also sharpens the reseed argument rather than softening it. Google is about to crawl `/blog` for the first time. Whether it crawls a hub linking to eleven interlinked posts or eleven orphans with blocked CTAs is decided by whether the reseed runs first.

**Search Console, last 30 days: 9 impressions, 0 clicks, all brand.** Every query is someone who already knows the name or is already in the product:

- `does tethered cost money` (position 1), `cost uk` (position 2), `tethered me` (position 8), `tethered app` (position 46), `tethered login` (position 80)
- `como me vinculo` (position 1), `juego solo` (position 1), `are there other options?` (position 4)

Two things worth noting. The Spanish queries and the phrasing of "are there other options?" look like in-product or assistant-mediated questions rather than typed searches, which fits the Chrome auto-translate guard that went in on 3 Oct. And the site ranks 1st for "does tethered cost money", so the pricing story is landing for anyone who asks. But there is still not one non-brand impression. Nobody is finding Tethered who did not already know it exists.

**Bing has the blog. Google does not.** `GetPageStats` shows `/blog/negotiating-consent-checklist` with **7 impressions**, more than the home page. That is the first organic blog impression recorded anywhere in this log. It is also a reminder that the Bing submission route is cheap and works: quota is 10,000/day and untouched.

### Search and AI-assistant landscape

Three searches. Tethered appeared in none of the three answers, which is now the eighth consecutive week of that.

**The discretion gap is real and it has held for two weeks.** I re-ran the "not out" query deliberately, to test whether last week's finding was a fluke. It was not. Asking how to set up a safe call for a kink date when you are not out returns no product, no tool, and no authoritative source. The assistant assembled an answer from a Xtra Magazine culture piece and some dating-app PR, and then reasoned its way to the generic fallback on its own: "select a trusted friend who respects your privacy". No citation, because there is nothing to cite. Same shape as last week, different sources, same hole.

That is a question with real search intent, real community vocabulary ("safe call" is a leatherfolk term, not marketing language), and literally nothing good ranking for it.

**The "best BDSM safety app" SERP got worse, not more competitive.** Last week it surfaced Ever Collar, BeMoreKinky and Apple Check In. This week the same territory returns KinkD (a dating app), a Patreon, a content-farm PDF generator and `publicspace.nyc` spam. The query is thin enough that the result set is unstable week to week. Read honestly, that cuts both ways: it is not a well-defended space, but it is also not a space with much volume behind it.

**The real finding: alternativeto.net is the ranking surface in this niche, and Tethered is not on it.** Four of the ten results for the D/s app comparison query were alternativeto.net pages (The Dynamic, Kneel, Obedience, SubTasks). More importantly, the AI-generated summary of those results lifted its verdict straight from the directory: "SubTasks is identified as the best Obedience alternative". That is an assistant citing a directory listing as authority.

This log has spent six weeks on owned content and never looked at directories. An LLM asked "what are the alternatives to Obedience" reads alternativeto.net and finds SubTasks, Kneel and The Dynamic. It cannot find Tethered, because Tethered has no entry. Listings there are free and user-submitted.

**New competitor logged: The Dynamic.** Surfaced on alternativeto.net as a D/s task manager and habit tracker. Not previously in this log or the overview. Worth a proper look before the next comparison post rewrite.

### Suggested post

Last week and the week before both pitched `safety-check-in-apps-compared`, an eight-section comparison against Apple Check In, Kitestring, Noonlight, Ever Collar and the rest. It has not been written either time. I am not pitching it a third time unchanged, because the reason it keeps not getting written is probably that it is a big research-heavy post about a field that moves every week, and this week's search results showed that field is unstable enough that the post would need rewriting by the time it ranked.

So: same opening, much smaller post, aimed at the one query that actually has no answer.

**Title:** Safe Calls When You're Not Out: How to Check In Without Outing Yourself
**Slug:** `safe-call-when-not-out`

**Targets:**
- "safe call kink", "how to do a safe call BDSM", "safe call not out", "kink date safety friend doesn't know"
- AI-assistant questions: "how do I set up a safe call if I'm not out about kink?", "what if I have nobody I can tell about a kink date?", "how do I stay safe meeting someone when I can't tell anyone where I'm going?", "is there a check-in app that doesn't require telling my contact what I'm doing?"

**Outline:**

- What a safe call actually is, in the community's own words. The leatherfolk custom: a friend who knows where you are, a mid-date check-in, an agreed deadline and an agreed escalation. Use the real vocabulary, because that is what people search
- The four things a safe call needs to work: a real deadline, a contact who has agreed in advance, enough information to act on, and a plan for what happens when the call does not come
- **The outing problem, which is the section that owns the query.** Every piece of standard safe-call advice assumes a contact you can be honest with. Most people in kink have at least one relationship where that is not true, and the usual answer is to skip the safe call entirely. That is the actual risk
- **What to tell someone without telling them everything.** The practical core of the post: an address, a time, a name, a "call me at 11 and if I don't pick up, call again, and if I still don't pick up, here is what to do". No disclosure of what the evening is. Scripts people can copy
- The case where there is nobody at all: an automated timer that escalates without a human in the loop, and what it can and cannot do. Link to `solo-play-safety-guide` and `meeting-new-partners-safely`
- Where apps fit, briefly and fairly. Apple's built-in Check In is free and good, and should be named as the right answer for plenty of people. What it assumes, and where a kink-aware alert differs. One short section, not the whole post
- The limit, stated plainly: every system escalates, none rescue. Emergency services first, always
- FAQ block for answer engines

**Why this one now:** it targets the only question in this space that two weeks of searching has failed to find a good answer for anywhere, and the gap is the kind LLMs fill by improvising, which is exactly the gap a citable page closes. It is also a fraction of the work of the comparison post, needs no competitor research that will be stale in a month, and Rob can write most of it from inside the scene without looking anything up. After three weeks of nothing shipping, the smaller post that gets written beats the better post that does not.

### Suggested site updates

Broken first.

1. **Run the reseed.** `AWS_PROFILE=personal npx tsx scripts/seed-blog-posts.ts`. Rob only, no AWS creds here. Fourth week on this list. One command, and it closes three separate fixes that are already written and merged: the comparison post's 2026 title and meta, the internal link graph, and every CTA off robots-blocked `/dashboard`. The new argument this week is timing: `/blog` is now Discovered in Google and will be crawled soon. Running this before that crawl is worth more than running it after.

2. **Strip the em dashes from the four original safety posts.** 74 of them, live on the site under the Tethered Team byline: `solo-play-safety-guide` (27), `negotiating-consent-checklist` (26), `meeting-new-partners-safely` (13), `when-things-go-wrong` (8). The six newer D/s posts are clean, so this is just the pre-rule content. It is a find-and-replace in the seed files and it rides along with item 1 at no extra cost, so do it in the same sitting.

3. **List Tethered on alternativeto.net.** Free, user-submitted, one sitting. This is the week's new finding and probably the best leverage on the list: the directory is four of the ten results for the main comparison query, and assistants quote its verdicts as authority. Add Tethered as an alternative to Obedience, Kneel and SubTasks, with the safety timer and the discretion angle as the differentiator. Every competitor is already there. This is the cheapest route into AI answers that this log has found.

Broader, and all small:

4. **Rewrite the `/blog` index meta description.** It currently reads "consent negotiation, scene safety, aftercare and more", which is the pre-pivot safety framing. Six of the eleven posts are D/s dynamic content now, and the home page repositioned a month ago. The blog index did not. One line of copy, and it is the page Google is about to crawl first.

5. **Fix the fireplay post.** Carried from last week, unchanged. `/blog/fireplay-101-a-beginner-s-guide-to-playing-with-fire-safely` has an auto-generated slug with the apostrophe mangled to "beginner-s", and it is the only live post with no source file in `scripts/blog-posts/`, so it cannot survive a reseed. Shorten to `fireplay-101` with a redirect, and write it back into the repo as a seed file. Two jobs, one sitting. Note the ordering risk: if item 1 runs before this one, check the fireplay post is still intact afterwards.

6. **Add the competitor set to `llms.txt`.** Carried. Still no mention of Ever Collar, BeMoreKinky, Apple Check In or now The Dynamic. One honest paragraph naming them and saying what Tethered does differently.

### Follow-ups for next week

- Did the reseed run. Same five-minute check: comparison post title, internal link count on two posts, no live post linking to `/dashboard`
- Did `/blog` move from Discovered to Crawled or Indexed. Two weeks of forward movement now, watch whether it continues without intervention
- Whether any individual post leaves "URL is unknown to Google"
- Bing: whether `/blog/negotiating-consent-checklist` holds its 7 impressions or grows, and whether any second post appears in `GetPageStats`
- The Dynamic: proper look at pricing, platform and positioning before the comparison post gets rewritten
- If the alternativeto.net listing goes in, whether it shows up in an AI answer within a few weeks. That is a clean, measurable test of the directory theory
