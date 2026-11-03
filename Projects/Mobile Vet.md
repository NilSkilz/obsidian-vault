# Mobile Vet

Freelance build for a potential client, not Rob's own venture: a mobile vet practice based in Gloucester (no specific area within Gloucestershire yet). Placeholder-named "The Mobile Vet" — that exact name is already trademarked-in-use by a UK practice (Queen's Award winner), so the recommended real name is "The Mobile Vet Co" (domain free). Waiting on Rob/client to confirm a real name.

Code lives at `~/projects/mobile-vet` (local git only).

## Marketing site
Single-page static site (hero, how it works, services, tabbed pricing, reviews marquee, areas, 4-step register wizard, emergency drawer), AI-generated photos. Live at https://mobilevet.cracky.co.uk (NPM host 21 → `.11:3070`, see `Context/Infrastructure.md`). Content is Gloucester-set (GL postcodes, local areas, 01452 numbers); placeholder vet name "Hannah".

## Admin price-list tool
`~/projects/mobile-vet/admin/prices.html` — turns the client's real CMA-format price list (the UK vet pricing transparency order) into a structured editable form: price items grouped into the client's 5 categories, multiple prices per item (by species/weight band, with an "add another" link), an Offered/Not-offered toggle that hides price boxes for N/A items, a client-facing note plus a private-only note per item, a "needs a price" counter, and a footnotes block (CMA */** asterisk markers, the £500-estimate line). Built 2026-11-03 from Rob's pasted real price sheet.

**Still needs a price (5 items):** nurse consultation, prescription fee for an additional item prescribed alongside another, repeat prescription fee.

**Open questions for the client, flagged in private notes:**
- Is "CYTO 1-3 £179.28" (cytology, ear swab) the external lab's charge to the practice, or the price charged to the client?
- Does the pre-surgical/pre-anaesthetic blood test price (£60 excl. SDMA / £90 incl.) include taking the sample, or is that separate?
