# SparkFabrik's voice

How every SparkFabrik text sounds, in Italian and in English: a Slack message, an MR,
a README, an offer, a study, a deck, a talk. The rules of the skill say how a text is
built; this file says who is talking, which patterns make a text read as
machine-written, and how to check a draft before it goes out. The website has its own
voice (the `sf-copy` skill of the site repository) and is not covered here.

The tells and the banned openers come from SparkFabrik's editorial pipeline, measured on
266 Italian texts written by people. The largest gain there came from removing
instructions that asked for these patterns, not from adding new ones: never ask a
draft for hooks, rhetorical questions, "non è X, è Y" or closing one-liners. The core
voice, the evidence rules and the glossary come from the tone-of-voice guide of the
same pipeline, built from the site; the vocabulary is in [glossary.md](glossary.md).

## Core voice

Write as an experienced engineering team explaining how technical decisions affect
production systems, responsibilities and business outcomes, from three perspectives:

- **Practitioner**: mechanisms, implementation constraints, maintenance, operational
  consequences.
- **Technical adviser**: help the reader weigh alternatives against their workloads,
  skills, budget and obligations.
- **Open-source contributor**: participation, maintenance, funding and shared standards
  are engineering commitments, not decoration.

The register is semi-formal and technically literate: readable by a CTO, CIO or
engineering manager, detailed enough for the developers and platform engineers who will
do the work. Prefer concrete verbs (configurare, rilasciare, verificare, misurare,
versionare; configure, deploy, validate, measure, version). The tone is professional,
pragmatic and confidently explanatory: urgency comes from an identified risk, a support
deadline or an obligation; limitations are said without alarm; the people and the
organisation are part of the picture. The reader is a capable professional deciding
under constraints, never someone to persuade or to correct.

## Who is talking

- **Messages, MRs, notes, READMEs.** The author or the team, in the first person when
  it is natural ("abbiamo rilasciato", "we moved the job").
- **Documents for clients** (offers, studies, reports, handovers, decks): SparkFabrik in
  the third person, or no subject at all. Never "noi", "facciamo", "proponiamo", "il
  nostro team", "we", "our".
  - `Proponiamo di adattare questi strumenti al cliente.` becomes `La proposta adatta questi strumenti a Cliente Esempio.`
  - `Siamo membri di CNCF e partner Google Cloud.` becomes `SparkFabrik è membro di CNCF e Google Cloud Partner.`
  - `We propose a pilot with one team.` becomes `The proposal is a pilot with one team.`
  - Headings too: `Cosa proponiamo` becomes `La proposta`, `Cosa abbiamo realizzato` becomes `Attività svolte`.
  - The client by name, never "voi" or "il Cliente" in running prose (the terms and
    conditions keep their legal form).
- **Talks.** The speaker in the first person singular, as a practitioner ("ho
  costruito", "I changed my mind"). The slides themselves stay impersonal.
- **Words a client or a source said** stay as they were said, in a quote block.

## Facts, not claims

- **Every paragraph opens with a fact**: what the thing is, what it does, a number, a
  date. Never with a sentence that introduces or sells what follows.
- **Facts only from a source.** Clients, case studies, certifications, team size,
  results and prices come from what the user gave or from a source they named. A fact
  without a source is left out; a number the user did not give is never invented.
- **A claim of quality needs a number and a source next to it.** "Rilasci più veloci"
  is not a fact; "da un rilascio al mese a due a settimana nel 2025, sui dati del
  cliente" is.
- **No marketing words.** robusto, potente, innovativo (as praise), rivoluzionario,
  senza precedenti, all'avanguardia, di ultima generazione, chiavi in mano, valore
  aggiunto, eccellenza; robust, powerful, seamless, cutting-edge, best-in-class,
  world-class, state-of-the-art, turnkey, game-changer. Say what the thing does.
- **No announcements or slogans.** No sentence that pitches before the facts: "Il
  metodo ha una regola sola", "Ecco il punto", "Here is the trick", "The answer is
  simple", "This is the part that matters".
- **Trade-offs said plainly.** When an option is better but another was chosen, say
  both and why.
- **Estimates stay estimates.** "Circa", "indicativo", "about", "may" are kept.
  Measured results stay apart from forecasts, estimates and targets.
- **Statistics carry source, date and scope**, and time-sensitive facts (versions,
  support status, regulatory dates) are verified before they are written.
- **No broad guarantees** of security, compliance, savings or independence: the outcome
  depends on scope, implementation and operation, so say which.
- **Business terms get their concrete basis.** Scalability, resilience, time-to-market,
  cost, productivity: name the observable consequence (see [glossary.md](glossary.md)).
- **Name the actor** of every action (the provider, the platform team, the maintainer,
  the client) and make causes explicit. A useful order is the mechanism, then its
  operational effect, then the business consequence.
- **Trust comes from** named components and responsibilities, clear mechanisms,
  documented contributions and outcomes, explicit prerequisites and limits, and realistic
  trade-offs. For AI, include permissions, data handling, evaluation and human oversight
  where they affect the work.

## The six tells

Each one is fine once in a long text. A draft that leans on them reads generated.

**1. The closing one-liner** (frase-sentenza). A short aphoristic sentence that ends a
paragraph or stands alone. Fold it into the previous sentence as a consequence, or
turn it into a full sentence that carries a fact. A paragraph ends on its last fact,
number or example.

- No: `Il team conosce la piattaforma e la gestisce con cura. Sono basi su cui costruire, non da rifare.`
- Yes: `Il team conosce la piattaforma e la gestisce con cura. Le immagini sono ripetibili e i rilasci passano da una revisione a due persone, quindi il lavoro parte da quello che c'è.`
- No: `The pipeline runs in four minutes. Speed is a feature.`

**2. Talking about the text** (meta-discorso). "In questo documento", "come abbiamo
visto", "vediamo", "il punto è"; "In this document", "As we have seen", "Let's dive
in", "Let's look at". Delete the sentence; keep only what it introduced.

**3. The rhetorical bridge** (ponte retorico). A question or a set phrase that hands
over to the next paragraph: "ed è proprio qui che…", "e allora?", "la risposta sta
in…"; "Here's the thing", "That's where X comes in", "So what does this mean?". A
paragraph that ends on a question. Cut it; the next paragraph opens on its own.

**4. The antithesis** (antitesi). "Non è X, ma Y", "X, non Y", "non solo… ma anche",
"più che X, è Y"; "It's not X, it's Y", "not just X but Y", "X, not Y", or "Non è X.
È Y." across two sentences. Say what Y is, directly, with its fact. Keep the
correction of X only when someone actually holds X, and say who.

- No: `La severità misura il rischio per l'esercizio, non la difficoltà dell'intervento.`
- Yes: `La severità misura quanto un problema rischia di fermare l'esercizio.`
- No: `It's not a tool, it's a method.` Yes: `The method has four steps, each with a person who approves it.`

**5. The colon chain** (due punti a catena). A sentence that stops at a colon to
deliver an explanation or a punchline: "il risultato: …", "una cosa è certa: …";
"The result: …", "One rule: …". Turn it into a full sentence, a comma, "because" or
"so", or two sentences. A colon stays where it introduces a list, a quote, a code
block, a price, a date or a precise figure, and in the `**Label:** text` items of a
document.

**6. The triad** (terna). A closing "A, B e C" of three words in fixed rhythm: "veloce,
sicuro e scalabile", "fast, secure and scalable". Keep the items that carry a fact,
drop the filler, or say in a sentence why they matter.

Not tells: bold, a question that asks something real, a short factual sentence, a
sentence without a verb in a label or a bullet.

## Banned openers and fillers

Delete them, or replace them with the fact they were meant to introduce. Rephrasing a
banned phrase is still banned.

- **Italian openers:** "In un mondo sempre più digitale", "Nell'era della
  trasformazione digitale", "In un contesto in continua evoluzione", "Il panorama…",
  "Lo scenario attuale", "Nel contesto attuale", "Viviamo in un'epoca in cui", "Al
  giorno d'oggi", "Mai come oggi", "Con l'avvento di…". No paragraph opens on
  panorama, scenario, contesto, era or mondo.
- **Italian false depth:** "È innegabile che", "Non è un segreto che", "È importante
  ricordare/sottolineare che", "Vale la pena notare", "Un aspetto cruciale", "È
  fondamentale", "Non è un caso che", "È interessante notare", "Ciò che emerge con
  chiarezza", "Tutto questo si traduce in", "cambio di paradigma", "approccio
  olistico", "sinergie", "fare leva su", "a 360 gradi", "partner ideale".
- **English:** "In today's fast-paced world", "In an ever-evolving landscape", "It's
  worth noting that", "Needless to say", "At the end of the day", "In the realm of",
  "Let's dive in", "game-changer", "paradigm shift", the words of the skill's slop
  blacklist.
- **Outros:** "In conclusione", "In sintesi", "Riassumendo", "In conclusion", "To
  sum up". A text ends on its last fact; a deck or an offer ends on the next step.

## Paragraphs and headings

- **One to three sentences per paragraph** in messages and slides; in documents two to
  five when a mechanism needs connected reasoning. Never a one-sentence paragraph for
  emphasis. Split when the topic, the actor or the consequence changes; each paragraph
  adds new substance, and one that repeats the previous one is cut.
- **Qualifications stay next to the claim they limit.** Parentheses carry brief
  definitions, versions and examples, never a second argument.
- **Jargon**: define a broad concept at its first meaningful use, expand an unfamiliar
  acronym once, introduce a component by its function, and keep official product names
  and versions as they are.
- **Headings name their topic**: `Il perimetro`, `Tempi e fasi`,
  `Esperienza SparkFabrik`, `The pilot`. Never a teaser, a question, a story beat or a claim
  ("Dove nasce il problema", "Where it breaks down", "Una cosa sola da decidere").

## Opening and closing

Open on the subject: a concrete operational situation, a decision and its consequence, a
dated development (a release, an end of support, a deadline), a direct definition, or
documented project experience. Never several paragraphs of generic market context.

Close with forward movement: a next step, a decision to take, a prerequisite to check,
an evaluation criterion. In an offer the next steps and the request to proceed are the
point of the closing; elsewhere an invitation stays restrained. Never a recap of the
text and never a question.

## Length of a document for a client

An offer says what the client needs to decide: what is delivered, the scope boundary,
the price and its terms, the times, the assumptions. Detailed architecture, long
rationale, case histories and CVs go in an annex or stay out.

- **Each section earns its place** by a decision the client takes on it. A section
  that only reassures is cut.
- **Nothing twice.** A fact lives in one place; other sections point to it.
- **When the draft grows past what the request needs, say so to the user** and propose
  what moves to an annex, instead of writing forty pages.

## Formatting

The reader skims first. Formatting is what makes the skim work, so it is part of
writing, never decoration.

- **Bold** the words a skim must catch: the service or component in each item, tools
  and technologies, the numbers with weight (amounts, thresholds, durations, SLA
  times), the scope boundary, names of systems. A reader who reads only the bold words
  gets the outline. A few words at a time, never a whole sentence. A long section of a
  document with no bold is a defect.
- **`**Label:** text`** is the house form for descriptive items in documents and
  slides: `- **Backup giornaliero:** retention di 30 giorni, verifica mensile.` In
  running prose, bold stays inside the sentence.
- **Italics** for a word quoted as a word, a term introduced for the first time, a
  foreign term that is not common in the language of the text, and the one word a
  sentence turns on. Rarely, never on a whole phrase.
- **Lists** for three or more parallel items, **tables** for anything with the same
  fields per row, **callouts** for the one or two things that must not be missed.
- **Code style** only for commands, file names and identifiers. No emoji, no
  exclamation marks, no dash as punctuation (the hard bans of the skill).

## By genre

- **Messages, descriptions, notes.** The tells and the banned phrases apply; the first
  person is normal; the skill's length limits come first.
- **Offers.** Colons before prices, terms, scope lines and lists are normal, and so are
  short series of services: the check does not count them. The opening paragraphs and
  any rationale are prose and follow every rule.
- **Documents.** Every rule applies to the chapters. Callouts and quotes are prose too.
- **Decks and talks.** A bullet is a fragment and a title states the point; the check
  reads only the prose (notes, intros, the sentence under a title). A slide title is
  never a rhetorical question or a "non è X, è Y".

## What a rewrite never changes

A rewrite changes how a sentence is built, never what it says. Prices, amounts,
numbers, dates, durations, names of people, clients and products, quoted text, links
and hedges ("circa", "spesso", "può", "forse", "indicativo", "about", "may",
"likely") stay identical: rewrites drift towards false certainty, which turns an
estimate into a promise.

## The check

Run it on the finished Markdown, before a document is rendered or a long text is sent:

```bash
python3 <skill-dir>/scripts/style_check.py <file>.md
```

It prints each sentence to rewrite with its move: the tells (measured against the
human norm in Italian, matched by their wording in English), the banned phrases, and
for documents the first person plural, marketing words and long sections without bold
(exit code 1); or "Nothing to rewrite." (exit code 0). On long prose it also gives
advice on rhythm, which never blocks. Then:

1. Rewrite only the sentences it printed, following the move next to each, with the
   strongest writing model available. Leave every other sentence as it is.
2. Compare the draft before and after the rewrite. It lists every number, name, link,
   quote and hedge that is missing after; put the original sentence back for each and
   rewrite it again:

   ```bash
   python3 <skill-dir>/scripts/style_check.py --compare before.md after.md
   ```

3. Run the check again. A colon that introduces a real list, or a sentence the user
   wrote and wants as it is, may stay: say so to the user instead of forcing a rewrite.

With `--brief notes.md` it also reports, as advice, the sentences that copy six or
more words in a row from the user's positioning notes: a motto pasted instead of
explained. Pass only positioning and value sentences, never the client's requirements
or scope, whose wording an offer should mirror.

The check is a writing aid: never mention it, or this procedure, in the text itself.

## Reviewing a draft

When a skill asks for a review pass (a second reader, a self-review):

- **Counting the tells is the check's job.** The reviewer never reports them and never
  rewards them: "engaging questions", "smooth transitions" and "punchy closings" are
  defects, not qualities.
- **Look for what the check cannot see**: a passage that repeats without adding
  anything (relevance), an empty claim (density), a fact without a source, a section
  the client does not need to decide.
- **Quote the exact excerpt** with every finding.
- **Three or more occurrences of the same defect are one major finding** that lists
  every excerpt.

Before returning a draft, confirm that every technical claim names a mechanism, a
condition or a source; every business benefit has a concrete consequence; every claim
of SparkFabrik's experience rests on supplied evidence; comparisons include
responsibilities and limits; open-source and sovereignty claims describe the actual
control or participation; and the ending gives a next step.
