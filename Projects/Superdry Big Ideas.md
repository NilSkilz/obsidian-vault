# Superdry: Big Projects & Ideas

Rob's running list of larger SD pieces (built, proposed, or always-talked-about-never-done). Compiled 26 Nov 2026 from Confluence, Slack, the PRISM Trello board and past Jarvis chats. Useful for BRP / 20% tech-debt pitches, appraisals and the CV.

Confluence base: https://supergroupbt.atlassian.net/wiki/spaces/TP

## 1. Platform & integration

### PRISM API (Rob's, in flight)
- Product data API over the PIM (Amplify Gen 2, Angular admin UI, API Gateway + Lambdas). Repo `SDryDigital/prism-api`.
- Built so far: products, `/sites` prices (PR #7), commodity code + country of origin (PR #12), prices for StraightLine (PR #11), npm client package with types + auth (PR #10, Jul 2026), image republish-to-SQS endpoint by season code.
- Consumers: StraightLine (replaced the ZigZag product feed), Marketplace Image Export (Next/Rithum zoom images), V11 category remap (Isaac, JWT service token).
- Auth roadmap (Trello "PRISM" board): Phases 1-2 done (Cognito + Azure AD SAML, frontend auth); 3-4 in progress (Lambda authoriser permissive, then scope enforcement); 5 to do (M2M clients + API-consumer UI); 6 backlog (split API into its own repo, frontend becomes plain OIDC client).
- **Next big step (Rob's own words, Jun 2026):** replace the SFCC product exporter with PRISM endpoints, it's the most comprehensive feed. Then write endpoints (POST to create PIM records). Niko helped improve the design.
- **Gap:** no PRISM overview page in Confluence, the Trello board and Slack PRs are the only record. Needs one if Rob wants credit for it (e.g. for BRP/appraisal).

### MuleSoft decommission
- Rob's view: business logic shouldn't live in MuleSoft; it's costly, brittle, and the Sep 2025 outage already forced the Nedap rebuild.
- Existing docs (Niko): [MuleSoft to AWS Native Migration Proposal](https://supergroupbt.atlassian.net/wiki/spaces/DigiForce/pages/4319608834) (Aug 2025, catalog/pricing/category to AWS), [Javelin ESB Apps Migration](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4546854915) (Jan 2026: 4 ESB apps (Schedulers, Styles-Colors, POs, Shipments) to Amplify Gen 2, ~18 days, **$900-1,800/mo down to $63-148/mo, 85-92% saving**), [Superdry Inventory Service Type-1](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4790353933) (Jun 2026, replaces the MuleSoft inventory app).
- Related idea: skip MuleSoft for product feeds entirely (SGP/PIM -> SFCC direct, via PRISM).

### Nedap migration (Rob's spike, partly done)
- [Current state + order](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4551999489) (Jan 2026): ID03/ID04 on AWS; ID05/06 still in Everest; ID07/07a still MuleSoft (ID07 dies with Pegasus); ID01 needs review. Plan: unified CDK stack, then migrate in that order.

### Off AP Worker / Rundeck
- [Migrating from AP Worker](https://supergroupbt.atlassian.net/wiki/spaces/DC/pages/3898179596) (Rob, Oct 2024): fact-find for moving jobs (Mercatus, Nedap, promotions, staff discount, Tarquin, V11) to TypeScript microservices. Isaac's V11 importer proposal (Oct 2026) continues it.

### New images infrastructure
- [New Images Infrastructure](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4663574530) (Rob, Apr 2026): one source of truth instead of many S3 buckets, tables and random IDs. Wider "photostudio image pipeline long-term plan" sits behind it. Rob's gripe: images should be an `<img>` on an API URL, not a fetch/store/export/import chain.

### PIM rewrite
- Rebuild the PIM UI (and arguably the PIM). Raised repeatedly with Ryan, Robert and Niko ("could do it over peak if there was any motivation from above", Nov 2026). No doc yet.

## 2. Delivery & engineering

- **Release Management Platform** ([concept](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4463558657), Rob, Nov 2025): one-click deploys of SFCC/SOM branches, environment state, rollback before deploy, no orphaned metadata, AT + approvals surfaced in one UI.
- **Streamlining non-prod** ([proposal](https://supergroupbt.atlassian.net/wiki/spaces/DC/pages/4097736992), Rob, Feb 2025): kill the fruit environments, consistent non-prod + serverless dev account.
- **Developers Handbook + ADRs** (Rob, Jan 2026): DoR/DoD, code review, testing, CDK over Serverless, event-driven over schedules. Done.
- **Agile Working Proposal** ([page](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4772528130), Jun 2026) and earlier [Summary of Ideas](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4380655617) (Oct 2025): refinement, points, retros, demos.
- **Automated testing for SFCC UI** (Nov 2026): Rob's stance is pilot + one-pager first. See Work Context.
- **Config Application** (Rob, Jan 2023): feature flags + params with UI, SDK, CLI. Never built, still relevant.

## 3. Storefront & commerce

- **Storefront Design Consistency Audit** ([draft](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4953178113), Rob, Oct 2026): fonts/colours/buttons, fixes by value and risk. Pairs with Robert Stanley's SFRA 6 -> 8 [Migration Plan](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/5008785410).
- **AI search** (Niko's [AI Powered Search Service](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4710432770) + [stock-aware cache](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4745822234)); Rob pushed Bedrock-with-fallback. Possible cheaper-Bloomreach angle.
- **Bloomreach Experiments SDK** (DGF-2757): spike first, then a refined ticket.
- **Bloomreach segments -> SFCC customer groups** ([page](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4606033921), Rob, Mar 2026).
- **AI product content** (from 19 Nov chat): descriptions, translations, alt text, attribute fill from PIM. Niko's [alt-text proposal](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4106452994) and the ai-service translations already exist.
- **FFS architecture rework** (DGF-3938, Rob, done May 2026) + [retrospective spec](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4730093580).

## 4. Channels & marketplaces

- **Delta feeds instead of full feeds** ([proposal](https://supergroupbt.atlassian.net/wiki/spaces/EC/pages/3366060034), Rob, May 2023) + [Channel Advisor cost saving](https://supergroupbt.atlassian.net/wiki/spaces/EC/pages/3372220441) (feeds cost ~$250/day, ~$91k/yr in AWS at the time).
- **GlobalBridge US marketplaces** ([page](https://supergroupbt.atlassian.net/wiki/spaces/TP/pages/4545675265), DGF-2684, Jan 2026).
- **Channels API** (Rob, 2023, Next is the only consumer).

## 5. Internal apps

- **StraightLine** (wholesale returns, replaces ZigZag, DGF-3405): Amplify app on PRISM, emails via SES still outstanding (Jun 2026).
- **Size guide generator** (DGF-1654, done).

## 6. Money-saving / vendor-replacement ideas (from Jarvis chats)
- Trustpilot (~£80k/yr): find out what it covers; Google Customer Reviews / Reviews.io / Feefo as a costed saving. (26 Nov 2026)
- Tills (~£2M), Nedap, Bloomreach, MuleSoft as "could we build it" targets. Verdict: MuleSoft is the real in-house win; tills/Nedap aren't. (19 Nov 2026)
- Conflict-of-interest/IP caveat applies to anything sold to SD rather than built as an employee.

## Rob's own shortlist (Slack to Ryan, 2 Jul 2026)
MuleSoft decommission, photostudio image processing plan, PIM UI rebuild, product feeds SGP -> SFCC skipping MuleSoft, new PRISM APIs, AI search. First pick: migrate the SFCC product exporter.
