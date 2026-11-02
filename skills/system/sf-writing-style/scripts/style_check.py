#!/usr/bin/env python3
"""Check a Markdown text against SparkFabrik's voice (references/voice.md), in Italian and in English.

Usage:
  python3 <skill-dir>/scripts/style_check.py <file.md> [--genre text|offer|doc|deck|talk] [--brief notes.md] [--json]
  python3 <skill-dir>/scripts/style_check.py --compare <before.md> <after.md>

What it reports, each with the sentence and the move to rewrite it (exit code 1), or "Nothing to rewrite." (0):
- the six tells. In Italian they are measured by style_meter.py (the style meter of the editorial pipeline) and reported when their rate is
  above the 90th percentile of human writing; in English they are matched by their wording ("It's not X, it's Y",
  "Here's the thing", "Let's dive in"). In offers, decks and talks colons and short series are normal (prices, terms,
  labels), so the colon chain and the triad are not counted there;
- the banned openers and fillers, in both languages;
- for documents, decks and talks: the first person plural (SparkFabrik speaks in the third person or impersonally;
  quotes of other people and talks are left out), marketing words, and long sections of an offer or a document with
  no bold at all.

Advice, which never changes the exit code: on Italian prose of 300 words or more (not on slides), a rhythm below the human floor
(sentence lengths too uniform, no parentheses); with --brief, the sentences that copy six or more words in a row from
the user's positioning notes (pass only positioning and value sentences, never the client's requirements).

--compare lists the numbers, names, links, quotes and hedges ("circa", "può", "about", "may") of the first file that
the second no longer has: a rewrite must keep them all (exit code 1 when one is missing).

The genre defaults to what the file is: a deck or a talk when it has `<!-- slide: -->` markers (a talk when it names an
`evento`), a document when its front matter has `tipo`, an offer when it names a `cliente`, a document when it names
an `evento` only, else plain text (a message, a description, a README, a spec, an ADR, with or without front matter).
Plain text gets the tells and the banned phrases only: the first person is normal there.

The language is the front matter's `lang` when there is one, else the one whose common words the prose uses most.
Issue and commit trailers (`Refs:`, `Closes:`, `Assisted-by:` …) and the AI attribution header are never read as prose.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_meter as sm  # noqa: E402  # pyright: ignore[reportMissingImports]

# One rewrite move per tell, as the editorial pipeline gives them, and their English twins.
MOVES = {
    'punch_sentence': "Frase-sentenza in chiusura: assorbila nel periodo precedente come conseguenza, o scioglila in "
                      "una frase completa che porti un fatto. Il paragrafo finisce sull'ultimo fatto, numero o "
                      "esempio, mai su uno slogan.",
    'meta_discourse': "Meta-discorso: togli la frase che parla del testo («in questo documento», «come abbiamo "
                      "visto», «il punto è»), non riformularla: resta solo ciò che introduceva.",
    'rhetorical_bridge': "Ponte retorico: taglia la domanda o la formula che passa al paragrafo seguente («ed è proprio "
                         "qui che…», una domanda in chiusura). Il paragrafo chiude sul suo ultimo fatto.",
    'antithesis': "Antitesi («non è X, ma Y», «X, non Y», «non solo… ma»): riscrivi in forma affermativa diretta, "
                  "dicendo che cosa è Y con il suo fatto.",
    'colon_chain': "Due punti a catena («il risultato: …»): sciogli i due punti in una frase compiuta o in una "
                   "virgola; tienili solo davanti a un elenco, una citazione o un dato preciso.",
    'triad': "Terna («veloce, sicuro e scalabile»): tieni gli elementi che portano un fatto e togli quello di "
             "riempimento, oppure sciogli l'elenco in una frase che dice perché.",
}
MOVES_EN = {
    'meta_discourse': "Talking about the text: delete the sentence (\"In this document\", \"Let's dive in\", \"As we have "
                      "seen\"); keep only what it introduced.",
    'rhetorical_bridge': "Rhetorical bridge: cut the question or set phrase that hands over to the next paragraph "
                         "(\"Here's the thing\", \"That's where X comes in\"); end the paragraph on its last fact.",
    'antithesis': "Antithesis (\"It's not X, it's Y\", \"not just X but Y\"): say what Y is, directly, with its fact.",
    'colon_chain': "Colon setup (\"The result: …\", \"One rule: …\"): write a full sentence, or join with because, so, "
                   "which; keep a colon only before a list, a quote, a code block or a precise figure.",
    'triad': "Triad (\"fast, secure and scalable\"): keep the items that carry a fact and drop the filler.",
}
EN_TELLS = [
    ('meta_discourse', re.compile(r"\b(?:in this (?:document|post|article|section|offer|study)|let's (?:dive|explore|look|"
                                  r"take a look|unpack)|as we(?: have|'ve)? seen|as mentioned (?:above|earlier)|"
                                  r"the (?:key )?point is)\b", re.I)),
    ('rhetorical_bridge', re.compile(r"\b(?:here's the thing|here is the thing|that's where .{1,40} comes? in|"
                                     r"and that's (?:exactly )?(?:where|why)|so what does (?:this|that) mean|"
                                     r"the answer (?:is simple|lies))\b", re.I)),
    ('antithesis', re.compile(r"\b(?:it(?:'s| is) not (?:just |only |about )?[^.,;:]{1,40}[,;:.] (?:it(?:'s| is)|but)|"
                              r"not just [^.,;]{1,40},? but|isn't [^.,;]{1,40}, it(?:'s| is))\b", re.I)),
    ('colon_chain', re.compile(r"\b(?:the (?:result|catch|trick|bottom line|answer|takeaway|good news)|one (?:rule|thing)"
                               r"(?: is (?:clear|certain))?|here's why|the twist):\s", re.I)),
]
EN_TRIAD = re.compile(r"\b(fast|secure|scalable|reliable|simple|robust|flexible|efficient|modern|powerful|easy),"
                      r" (fast|secure|scalable|reliable|simple|robust|flexible|efficient|modern|powerful|easy),? and "
                      r"(fast|secure|scalable|reliable|simple|robust|flexible|efficient|modern|powerful|easy)\b", re.I)

# Banned openers and fillers: the editorial pipeline's seed list for Italian, and the English ones of voice.md. Case-insensitive.
BANNED = [
    "in un mondo sempre più digitale", "nell'era della trasformazione digitale", "in un contesto in continua evoluzione",
    "la crescente complessità", "il panorama digitale", "in continua evoluzione", "nel panorama", "lo scenario attuale",
    "nel contesto attuale", "il contesto di business odierno", "viviamo in un'epoca in cui", "al giorno d'oggi",
    "una vera e propria rivoluzione", "con l'avvento di", "mai come oggi", "sta attraversando una fase di",
    "in questo documento esploreremo", "scopriamo insieme", "andiamo a scoprire", "è innegabile che",
    "non è un segreto che", "non va sottovalutato", "è importante ricordare che", "è importante sottolineare",
    "vale la pena sottolineare", "vale la pena notare", "un aspetto cruciale", "è fondamentale",
    "un vero e proprio cambio di paradigma", "cambio di paradigma", "diventa cruciale",
    "la domanda che molti si pongono", "tutto questo si traduce in", "ciò che emerge con chiarezza",
    "è ormai assodato", "non è un caso che", "è interessante notare", "all'avanguardia", "approccio olistico",
    "sinergie", "fare leva su", "a 360 gradi", "in conclusione", "in sintesi", "riassumendo",
    "partner ideale", "il partner giusto",
]
BANNED_EN = [
    "in today's fast-paced world", "in today's digital world", "in an ever-evolving", "ever-changing landscape",
    "it's worth noting", "it is worth noting", "needless to say", "at the end of the day", "in the realm of",
    "game-changer", "game changer", "paradigm shift", "in conclusion", "to sum up", "delve into", "unlock the power",
    "take it to the next level", "a testament to", "plays a crucial role", "navigate the complexities",
]

# The voice of client documents: SparkFabrik in the third person or impersonal, no marketing words, bold on what a
# skim must catch. A talk is spoken in the first person by its speaker, so it is not checked for the first person.
FIRST_PERSON = re.compile(r"\b(?:[a-zàèéìòù]+iamo|noi|nostr[oaie])\b", re.I)
MARKETING = re.compile(r"\b(?:robust[oaie]|potent[ei]|rivoluzionari[oae]?|senza precedenti|di ultima generazione|"
                       r"best[- ]in[- ]class|chiavi in mano|valore aggiunto|eccellenz[ae]|game[- ]changer|next level|"
                       r"a tutto tondo|all'avanguardia|innovativ[oaie] e)\b", re.I)
# "us" only in lower case and not before a hyphen, so "US" and "us-east-1" are not read as the first person.
FIRST_PERSON_EN = re.compile(r"\b(?:[Ww]e|WE|[Oo]urs?|OURS?)\b|\bus\b(?!-)")
MARKETING_EN = re.compile(r"\b(?:robust|powerful|seamless(?:ly)?|cutting[- ]edge|best[- ]in[- ]class|state[- ]of[- ]the[- ]art|"
                          r"game[- ]changer|next[- ]level|world[- ]class|turnkey|revolutionary|unparalleled|holistic)\b", re.I)
VOICE_MOVES = {
    'first_person': "Prima persona plurale (we, our): SparkFabrik come soggetto, oppure la frase impersonale "
                    "(«proponiamo di adattare» diventa «la proposta adatta»; «we propose» diventa «the proposal is»).",
    'marketing': "Parola da pubblicità: di' che cosa fa la cosa, con un numero e la sua fonte, oppure togli l'aggettivo.",
    'no_bold': "Sezione lunga senza grassetto: metti in grassetto le parole che chi scorre deve cogliere "
               "(il servizio, gli strumenti, i numeri con peso, il confine del perimetro), poche parole alla volta.",
}
VOICE_MOVES_EN = {
    'first_person': "First person plural (we, our): make SparkFabrik the subject, or write the sentence impersonally "
                    "(\"we propose a pilot\" becomes \"the proposal is a pilot\").",
    'marketing': "Marketing word: say what the thing does, with a number and its source, or drop the adjective.",
    'no_bold': "Long section without bold: bold the words a skimming reader must catch (the service, the tools, the "
               "numbers with weight, the scope boundary), a few words at a time.",
}
# Common words of each language, used to tell the language of a text without `lang` in its front matter.
COMMON_IT = frozenset("il lo la gli le di del della dei delle che è non per con una sono nel nella alla anche più come "
                      "questo questa ma se ci si al".split())
COMMON_EN = frozenset("the of and to is are that for with this not be was it as on by or from have has will can "
                      "which an but".split())
NO_BOLD_WORDS = 150
RHYTHM_WORDS = 300
ECHO_WORDS = 6

OFF = {'offer': {'colon_chain', 'triad'}, 'deck': {'colon_chain', 'triad'}, 'talk': {'colon_chain', 'triad'}, 'doc': set(),
       'text': set()}


def front_matter(text):
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        if v and not line.startswith(' '):
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, text[m.end():]


# Lines that are references or signatures, never prose: issue and MR trailers, commit trailers, the AI attribution
# header of the gh and glab skills.
TRAILER = re.compile(r"^(?:>\s*:robot:|(?:refs|closes|fixes|resolves|related|part of|see also|assisted-by|co-authored-by|"
                     r"signed-off-by|reviewed-by)\s*:)", re.I)
def prose_markdown(body):
    """The text as the meter reads it: the `::: block attrs` and `:::` fences of sf-docs become blank lines, so a
    callout or a quote keeps its prose but its attributes are not read as a sentence."""
    out = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith(':::') or s.startswith('<!--') or s.startswith('{{') or TRAILER.match(s):
            out.append('')
        else:
            out.append(line)
    return '\n'.join(out) + '\n'


def voice_lines(body):
    """The lines that speak in SparkFabrik's voice: everything but quotes of other people (`::: quote` blocks and plain
    `>` quotes; a `> **Nota:**` callout is ours), code, comments and tables of figures."""
    out, quote, code = [], False, False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith('```'):
            code = not code
            continue
        if code or s.startswith('<!--'):
            continue
        if s.startswith(':::'):
            quote = s.startswith('::: quote') if s != ':::' else False
            continue
        if quote or (s.startswith('>') and not s.lstrip('> ').startswith('**')):
            continue
        out.append(line)
    return out


def voice(body, genre, lang='it'):
    issues = []
    if genre == 'text':
        return issues
    lines = voice_lines(body)
    fp, mk, moves = (FIRST_PERSON_EN, MARKETING_EN, VOICE_MOVES_EN) if lang == 'en' else (FIRST_PERSON, MARKETING, VOICE_MOVES)
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if genre != 'talk':
            for m in fp.finditer(text):
                issues.append({'issue': 'first_person', 'word': m.group(0), 'text': text[:220], 'move': moves['first_person']})
                break
        for m in mk.finditer(text):
            issues.append({'issue': 'marketing', 'word': m.group(0), 'text': text[:220], 'move': moves['marketing']})
            break
    if genre in ('offer', 'doc'):
        section, words, bold = None, 0, False

        def close():
            if section and words >= NO_BOLD_WORDS and not bold:
                issues.append({'issue': 'no_bold', 'word': '', 'text': section, 'move': moves['no_bold']})
        for line in lines:
            s = line.strip()
            if re.match(r'^#{1,3} ', s):
                close()
                section, words, bold = s.lstrip('# ').strip(), 0, False
            elif s and not s.startswith('|'):
                words += len(s.split())
                bold = bold or '**' in s
        close()
    return issues


def english_tells(md, genre):
    """The tells in English, matched by their wording on the prose paragraphs (the meter is calibrated on Italian)."""
    off = OFF.get(genre, set())
    tells = []
    for p in sm.extract_prose(md):
        sentences = sm.split_sentences(p.text)
        for s in sentences:
            for kind, rx in EN_TELLS:
                if kind not in off and rx.search(s):
                    tells.append({'tell': kind, 'sentence': s.strip(), 'move': MOVES_EN[kind]})
            if 'triad' not in off and EN_TRIAD.search(s):
                tells.append({'tell': 'triad', 'sentence': s.strip(), 'move': MOVES_EN['triad']})
        if sentences and sentences[-1].strip().endswith('?') and len(sentences) > 1:
            tells.append({'tell': 'rhetorical_bridge', 'sentence': sentences[-1].strip(), 'move': MOVES_EN['rhetorical_bridge']})
    return tells


def rhythm_advice(m, genre):
    if m.word_count < RHYTHM_WORDS or genre in ('deck', 'talk'):
        return []
    return [{'measure': k, 'value': round(r.value, 2), 'floor': round(r.p10, 2), 'advice': r.description}
            for k, r in (m.rhythm or {}).items() if r.below]


def _words(text):
    return re.findall(r"[a-zàèéìòù']+", text.lower())


def brief_echo(md, brief):
    """Sentences of the text that copy ECHO_WORDS or more words in a row from a line of the brief (quoted text and
    numbers do not count)."""
    grams = set()
    for line in brief.splitlines():
        w = _words(re.sub(r'«[^»]*»|"[^"]*"', ' ', line))
        grams |= {tuple(w[i:i + ECHO_WORDS]) for i in range(len(w) - ECHO_WORDS + 1)}
    out = []
    for p in sm.extract_prose(md):
        for s in sm.split_sentences(p.text):
            w = _words(re.sub(r'«[^»]*»|"[^"]*"', ' ', s))
            if any(tuple(w[i:i + ECHO_WORDS]) in grams for i in range(len(w) - ECHO_WORDS + 1)):
                out.append(s.strip())
    return out


def check(text, genre=None, brief=None):
    meta, body = front_matter(text)
    genre = genre or guess_genre(meta, body)
    md = prose_markdown(body)
    lang = guess_lang(meta, md)
    advice = {'rhythm': [], 'brief_echo': brief_echo(md, brief) if brief else []}
    if lang == 'en':
        banned = [{'phrases': list(h.phrases), 'sentence': h.excerpt.strip()} for h in sm.find_phrases(md, BANNED_EN)]
        words = sum(len(p.text.split()) for p in sm.extract_prose(md))
        return {'genre': genre, 'lang': 'en', 'words': words, 'tells': english_tells(md, genre), 'banned': banned,
                'voice': voice(body, genre, 'en'), 'advice': advice}
    enabled = frozenset(k for k in sm.TELL_KINDS if k not in OFF.get(genre, set()))
    m = sm.measure(md, sm.StyleMeterSettings(enabled=enabled))
    tells = []
    for f in m.flagged:
        for h in f.hits:
            if h.kind in m.tells_above:
                tells.append({'tell': h.kind, 'sentence': h.sentence.strip(), 'move': MOVES[h.kind]})
    banned = [{'phrases': list(h.phrases), 'sentence': h.excerpt.strip()} for h in sm.find_phrases(md, BANNED)]
    advice['rhythm'] = rhythm_advice(m, genre)
    rates = {k: round(v.per_1000, 1) for k, v in m.measures.items() if v.enabled}
    return {'genre': genre, 'lang': 'it', 'words': m.word_count, 'rates': rates, 'above': list(m.tells_above),
            'tells': tells, 'banned': banned, 'voice': voice(body, genre), 'advice': advice}


def guess_lang(meta, md):
    if meta.get('lang'):
        return 'en' if meta['lang'].lower().startswith('en') else 'it'
    words = re.findall(r"[a-zàèéìòù]+", md.lower())
    return 'en' if sum(w in COMMON_EN for w in words) > sum(w in COMMON_IT for w in words) else 'it'


def guess_genre(meta, body=''):
    if '<!-- slide:' in body:
        return 'talk' if (meta.get('evento') or '<!-- slide: talk' in body) else 'deck'
    if meta.get('tipo'):
        return 'doc'
    if meta.get('cliente'):
        return 'offer'
    if meta.get('evento'):
        return 'doc'
    return 'text'


HEDGES = re.compile(r"\b(?:circa|spesso|può|possono|potrebbe|potrebbero|forse|indicativ[oaie]|stimat[oaie]|fino a|"
                    r"about|around|roughly|approximately|may|might|likely|often|up to|estimated)\b", re.I)


def facts(text):
    """What a rewrite must keep: numbers, names (capitalised words not opening a sentence), links, quotes, hedges."""
    _, body = front_matter(text)
    found = {'numbers': set(re.findall(r"\d[\d.,]*\s?(?:%|€|euro|k€|ore|giorni|mesi|anni)?", body)),
             'links': set(re.findall(r"\]\(([^)]+)\)|(https?://\S+)", body)),
             'quotes': set(re.findall(r'«[^»]{3,}»|"[^"\n]{3,}"', body)),
             'hedges': set(h.lower() for h in HEDGES.findall(body)),
             'names': set()}
    found['links'] = {a or b for a, b in found['links']}
    found['numbers'] = {n.strip().rstrip('.,') for n in found['numbers']}
    for sentence in re.split(r'(?<=[.!?:])\s+|\n', body):
        for w in re.findall(r"(?<=\s)[A-ZÀ-Ý][\w&.-]+", ' ' + sentence.strip())[1:]:
            found['names'].add(w.rstrip('.,;:'))
    return found


def compare(before, after):
    a, b = facts(before), facts(after)
    return {k: sorted(a[k] - b[k]) for k in a if a[k] - b[k]}


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n\n')[0])
    ap.add_argument('draft', nargs='?')
    ap.add_argument('--genre', choices=sorted(OFF))
    ap.add_argument('--brief', help='the user\'s positioning notes, one formula per line (advice only)')
    ap.add_argument('--compare', nargs=2, metavar=('BEFORE', 'AFTER'))
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if a.compare:
        for f in a.compare:
            if not os.path.isfile(f):
                print(f'No such file: {f}', file=sys.stderr)
                return 2
        lost = compare(open(a.compare[0], encoding='utf-8').read(), open(a.compare[1], encoding='utf-8').read())
        if a.json:
            print(json.dumps(lost, ensure_ascii=False, indent=1))
        elif not lost:
            print('Every number, name, link, quote and hedge is still there.')
        else:
            for k, v in lost.items():
                print(f"Missing {k}: {', '.join(v)}")
            print('Put the original sentence back for each, then rewrite it again keeping them.')
        return 1 if lost else 0
    if not a.draft or not os.path.isfile(a.draft):
        print(f'No such file: {a.draft}', file=sys.stderr)
        return 2
    brief = open(a.brief, encoding='utf-8').read() if a.brief else None
    r = check(open(a.draft, encoding='utf-8').read(), a.genre, brief)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"{a.draft}: {r['genre']}, {r['lang']}, {r['words']} words of prose.")
        if not r['tells'] and not r['banned'] and not r['voice']:
            print('Nothing to rewrite.')
        for t in r['tells']:
            print(f"\n[{t['tell']}] {t['sentence']}\n  {t['move']}")
        for b in r['banned']:
            print(f"\n[banned: {', '.join(b['phrases'])}] {b['sentence']}\n  Delete it or replace it with the fact it "
                  f"was meant to introduce; if the sentence existed only for it, delete the sentence.")
        for v in r['voice']:
            where = f"«{v['word']}» in: " if v['word'] else 'section: '
            print(f"\n[{v['issue']}] {where}{v['text']}\n  {v['move']}")
        for x in r['advice']['rhythm']:
            print(f"\n[advice: rhythm] {x['measure']} {x['value']} under the human floor {x['floor']}. {x['advice']}")
        for s in r['advice']['brief_echo']:
            print(f"\n[advice: brief echo] {s}\n  The sentence repeats the notes word for word: explain the idea with a fact.")
    return 1 if (r['tells'] or r['banned'] or r['voice']) else 0


if __name__ == '__main__':
    sys.exit(main())
