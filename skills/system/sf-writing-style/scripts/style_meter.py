# The style meter of SparkFabrik's editorial pipeline: the code is the same, the comments are trimmed.
# style_check.py adapts it to documents, decks and short texts.
"""Deterministic style meter: structural tells of machine prose, per 1000 words.

The meter measures six structural tells on the prose of an Italian Markdown
article and compares each rate with the norm measured on human-written Italian
articles (SparkFabrik's own up to 2023-03 plus a reference outlet corpus). It is pure standard library on purpose,
so it gives identical numbers wherever it runs.

Tells (per 1000 prose words):

- ``meta_discourse``: sentences that talk about the text itself («In questo
  articolo», «Come abbiamo visto», «Riassumendo», «Il punto è»).
- ``rhetorical_bridge``: a rhetorical question or a set phrase used to hand
  the reader to the next passage («Ed è esattamente qui che…», a paragraph
  that ends on a question).
- ``punch_sentence``: a short aphoristic sentence that closes a paragraph or
  stands alone as one («Il resto è dettaglio.») , the «build-build-punch»
  cadence. Short factual sentences and short openings are not counted: the
  reference corpora show good writers use both.
- ``antithesis``: the «non è X, è Y» family («non solo … ma», «più che … è»,
  «X, non Y», «Non è X. È Y.» across two sentences).
- ``colon_chain``: a sentence that hangs its explanation on a colon.
- ``triad``: a closing «A, B e C» of lower-case words; proper nouns, phrases
  with function words and the tail of a longer list are not counted.

Bold emphasis and rhetorical questions in general are NOT tells: the human
corpus uses both as much as or more than the machine drafts do.

Headings, lists, blockquotes, tables, code, footnote definitions, front
matter, HTML blocks and Hugo shortcodes are excluded from numerator and
denominator: only prose paragraphs are measured.

Calibration: ``HUMAN_NORM`` holds the median and the 90th percentile of each
tell over the human corpus. Thresholds default to the 90th percentile.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Literal, Mapping, Optional

TellKind = Literal[
    "meta_discourse",
    "rhetorical_bridge",
    "punch_sentence",
    "antithesis",
    "colon_chain",
    "triad",
]

TELL_KINDS: tuple[TellKind, ...] = (
    "meta_discourse",
    "rhetorical_bridge",
    "punch_sentence",
    "antithesis",
    "colon_chain",
    "triad",
)

#: Document-level rhythm measures. Unlike the tells they are
#: ABSENCE signals: machine prose has too few parentheses and sentences of
#: too similar a length, so the human band is a floor (10th percentile), not
#: a ceiling, and no paragraph is flagged for them.
RhythmKind = Literal["sentence_length_cv", "parentheses"]
RHYTHM_KINDS: tuple[RhythmKind, ...] = ("sentence_length_cv", "parentheses")

#: Italian labels for the UI. Kept here so every surface names a tell the same way.
TELL_LABELS_IT: dict[str, str] = {
    "meta_discourse": "Meta-discorso",
    "rhetorical_bridge": "Ponte retorico",
    "punch_sentence": "Frase-sentenza",
    "antithesis": "Antitesi",
    "colon_chain": "Due punti a catena",
    "triad": "Terna",
}
RHYTHM_LABELS_IT: dict[str, str] = {
    "sentence_length_cv": "Ritmo delle frasi",
    "parentheses": "Incisi tra parentesi",
}

#: One-line Italian explanations for settings and cards.
TELL_DESCRIPTIONS_IT: dict[str, str] = {
    "meta_discourse": "Frasi che parlano del testo stesso o annunciano quello che sta per dire («in questo articolo», «come abbiamo visto», «la risposta è semplice: …»).",
    "rhetorical_bridge": "Domande o formule usate per passare al paragrafo seguente («ed è proprio qui che…»).",
    "punch_sentence": "Frase breve e sentenziosa che chiude il paragrafo o sta da sola («Il resto è dettaglio.»), senza fatti, numeri o nomi.",
    "antithesis": "Costruzioni «non è X, è Y», «X, non Y», «non solo… ma», «più che… è», anche spezzate in due frasi («Non è X. È Y.»).",
    "colon_chain": "Frasi che agganciano la spiegazione con i due punti («il risultato: …», «una cosa è certa: …»).",
    "triad": "Terne di aggettivi o concetti a ritmo fisso («veloce, sicuro e scalabile»); nomi propri ed elenchi più lunghi non contano.",
}
RHYTHM_DESCRIPTIONS_IT: dict[str, str] = {
    "sentence_length_cv": "Quanto varia la lunghezza delle frasi (deviazione sulla media): la prosa umana alterna frasi lunghe e brevi, quella macchina le tiene tutte uguali.",
    "parentheses": "Incisi tra parentesi ogni 1000 parole: chi scrive per mestiere li usa, il modello quasi mai.",
}


@dataclass(frozen=True)
class HumanNorm:
    """Median and 90th percentile of a tell on the human corpus (per 1000 words)."""

    median: float
    p90: float


#: Calibrated on human Italian prose: the SparkFabrik articles published up to
#: 2023-03 (written by many different authors, so the norm is a pooled band, not
#: one house style) plus about 200 articles from Il Tascabile, Valigia Blu,
#: Nuovo e Utile, MokaByte, Guerre di Rete, Wired Italia and Il Disinformatico
#: Later SparkFabrik articles are left out: they may already carry
#: machine-assisted writing. Recalibrate on the same corpora whenever a pattern
#: list changes; the numbers come from a measurement, never typed by hand.
HUMAN_NORM: dict[str, HumanNorm] = {
    # Recalibrated 2026-09-23 on 266 documents after a blind
    # strict read of five machine drafts and three human controls: meta and
    # antithesis detectors widened (they missed most of what a reader marks),
    # triad narrowed to three single lower-case words closing a clause (it counted
    # phrases and longer lists). Previous norm: 0.4/1.9, 0.0/1.4, 0.5/2.6, 0.9/3.0,
    # 5.0/9.1, 3.8/7.3.
    "meta_discourse": HumanNorm(median=0.4, p90=1.6),
    "rhetorical_bridge": HumanNorm(median=0.0, p90=1.5),
    "punch_sentence": HumanNorm(median=0.7, p90=2.7),
    "antithesis": HumanNorm(median=1.0, p90=3.1),
    "colon_chain": HumanNorm(median=5.4, p90=9.3),
    "triad": HumanNorm(median=0.3, p90=1.5),
}


@dataclass(frozen=True)
class RhythmNorm:
    """10th percentile and median of a rhythm measure on the human corpus."""

    p10: float
    median: float


#: Same corpora and cutoff as ``HUMAN_NORM``.
RHYTHM_NORM: dict[str, RhythmNorm] = {
    "sentence_length_cv": RhythmNorm(p10=0.42, median=0.55),
    "parentheses": RhythmNorm(p10=0.5, median=4.3),
}

#: The meter's definitions and norm, as a version. Bump it with
#: the date whenever a detector or ``HUMAN_NORM`` changes: a measurement taken
#: under another version is not comparable, and the widget says so instead of
#: letting the editor read the difference as the effect of their edits.
METER_VERSION = "2026-09-23"
METER_CHANGE_NOTE_IT = (
    "Metro aggiornato il 23 settembre 2026: meta-discorso, antitesi e terna ridefiniti e norma "
    "ricalcolata. Le misure prese prima di questa data non sono confrontabili con quelle di oggi."
)

DEFAULT_PUNCH_MAX_WORDS = 9


@dataclass(frozen=True)
class StyleMeterSettings:
    """What the meter compares against. Defaults are the human 90th percentile."""

    thresholds: Mapping[str, float] = field(
        default_factory=lambda: {k: v.p90 for k, v in HUMAN_NORM.items()}
    )
    enabled: frozenset[str] = field(default_factory=lambda: frozenset(TELL_KINDS))
    punch_max_words: int = DEFAULT_PUNCH_MAX_WORDS
    #: Document-level rhythm measures (advisory, never flag a paragraph).
    rhythm_enabled: bool = True

    def threshold_for(self, kind: str) -> float:
        return float(self.thresholds.get(kind, HUMAN_NORM[kind].p90))


# ---------------------------------------------------------------------------
# Prose extraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProseParagraph:
    """A prose paragraph with its position in the original Markdown."""

    index: int
    text: str
    start: int
    end: int


_FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
_FENCE_RE = re.compile(r"^(```|~~~)")
_HEADING_RE = re.compile(r"^#{1,6}\s")
_BLOCKQUOTE_RE = re.compile(r"^\s*>")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_TABLE_RE = re.compile(r"^\s*\|")
_FOOTNOTE_DEF_RE = re.compile(r"^\s*\[\^[^\]]+\]:")
# HTML lines are excluded unless they are prose paragraphs or inline markup.
_HTML_BLOCK_RE = re.compile(r"^\s*<(?!(?:p|strong|em|b|i|a|span|br|code|sup|sub)\b)[a-zA-Z/!]")
_SHORTCODE_RE = re.compile(r"^\s*\{\{[<%]")
_IMAGE_LINE_RE = re.compile(r"^\s*!\[")
_HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_META_LINE_RE = re.compile(r"^\*\*(?:Autore|Pubblicato|Tags)\b.*$", re.I)

_INLINE_SHORTCODE_RE = re.compile(r"\{\{[<%].*?[%>]\}\}", re.S)
_INLINE_HTML_RE = re.compile(r"</?[a-zA-Z][^>]{0,200}>")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1", re.S)
_CODE_SPAN_RE = re.compile(r"`[^`]*`")


def _plain_text(paragraph: str) -> str:
    """Markdown paragraph → plain prose (links keep their text, markers stay)."""

    text = _INLINE_SHORTCODE_RE.sub(" ", paragraph)
    text = _CODE_SPAN_RE.sub(" ", text)
    text = _INLINE_HTML_RE.sub(" ", text)
    text = _LINK_RE.sub(r"\1", text)
    # Emphasis is not a tell: drop the markers, keep the words.
    for _ in range(2):
        text = _EMPHASIS_RE.sub(r"\2", text)
    text = text.replace("\n", " ")
    return re.sub(r"[ \t]{2,}", " ", text).strip()


_HTML_ELEMENT_RE = re.compile(
    r"<(div|span|script|style|iframe|figure|table|details|aside|nav|footer|header)\b[^>]*>.*?</\1\s*>",
    re.S | re.I,
)
_LINE_EXCLUDE_RES = (
    _HEADING_RE,
    _BLOCKQUOTE_RE,
    _LIST_RE,
    _TABLE_RE,
    _FOOTNOTE_DEF_RE,
    _HTML_BLOCK_RE,
    _SHORTCODE_RE,
    _IMAGE_LINE_RE,
    _HR_RE,
    _META_LINE_RE,
)
_BLOCK_RE = re.compile(r"(?:[ \t]*\S[^\n]*\n?)+")


def _blank_html_elements(body: str) -> str:
    """Replace block HTML elements with whitespace of the same length.

    Offsets stay valid and the element's lines become blank, so the prose
    that follows it on the next line starts a block of its own.
    """

    def blank(m: "re.Match[str]") -> str:
        return "".join("\n" if ch == "\n" else " " for ch in m.group(0))

    previous = None
    text = body
    # Nested elements: a few passes are enough for article markup.
    for _ in range(4):
        if text == previous:
            break
        previous = text
        text = _HTML_ELEMENT_RE.sub(blank, text)
    return text


def extract_prose(markdown: str) -> list[ProseParagraph]:
    """Return the prose paragraphs of a Markdown document with their offsets.

    A block is a run of non-blank lines. Inside a block, lines that are
    headings, list items, quotes, tables, footnote definitions, shortcodes,
    images, rules or HTML are dropped; the remaining lines form one prose
    paragraph. Fenced code and block HTML elements are removed first.

    Args:
        markdown: The article body (front matter allowed).

    Returns:
        Paragraphs in document order; ``text`` is plain prose, ``start``/``end``
        are offsets of the original block inside ``markdown``.
    """

    if not markdown:
        return []
    offset = 0
    fm = _FRONT_MATTER_RE.match(markdown)
    if fm:
        offset = fm.end()
    body = _blank_html_elements(markdown[offset:])

    paragraphs: list[ProseParagraph] = []
    in_fence = False
    index = 0
    for m in _BLOCK_RE.finditer(body):
        block = m.group(0).strip("\n")
        lines = block.split("\n")
        kept: list[str] = []
        for line in lines:
            stripped = line.strip()
            if _FENCE_RE.match(stripped):
                in_fence = not in_fence
                continue
            if in_fence or not stripped:
                continue
            if any(rx.match(line) for rx in _LINE_EXCLUDE_RES):
                continue
            kept.append(stripped)
        if not kept:
            continue
        text = _plain_text(" ".join(kept))
        if not text:
            continue
        paragraphs.append(
            ProseParagraph(index=index, text=text, start=offset + m.start(), end=offset + m.end())
        )
        index += 1
    return paragraphs


# ---------------------------------------------------------------------------
# Sentences
# ---------------------------------------------------------------------------

_ABBREVIATIONS = {
    "dott", "prof", "ing", "avv", "sig", "sra", "dr", "es", "ecc", "cfr",
    "fig", "tab", "vol", "cap", "pag", "n", "nr", "tel", "fax", "p", "pp",
    "art", "sec", "min", "max", "ca", "vs",
}
_SENTENCE_END_RE = re.compile(r"(?<=[.!?…])\s+(?=[\"“«(]?[A-ZÀÈÉÌÒÙ0-9])")
_WORD_RE = re.compile(r"\b\w[\w'’]*\b")


def split_sentences(text: str) -> list[str]:
    """Split plain prose into sentences, Italian-aware, keeping short ones.

    Unlike the variety analyser's splitter this keeps two-word sentences: the
    punch tell is precisely about them.
    """

    parts = _SENTENCE_END_RE.split(text)
    sentences: list[str] = []
    buffer = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        candidate = f"{buffer} {part}".strip() if buffer else part
        last = re.search(r"(\w+)\.$", buffer) if buffer else None
        if last and last.group(1).lower() in _ABBREVIATIONS:
            buffer = candidate
            continue
        if buffer:
            sentences.append(buffer)
        buffer = part
    if buffer:
        sentences.append(buffer)
    return sentences


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# Tell detectors
# ---------------------------------------------------------------------------

_META_DISCOURSE_RE = re.compile(
    r"\b(?:"
    r"in quest[oa] (?:articolo|pezzo|post|testo|paragrafo|guida|sezione|capitolo)"
    r"|(?:come|lo) (?:abbiamo|avevamo|ho) (?:visto|detto|anticipato|scritto|accennato|raccontato)"
    r"|come vedremo|come vedrai|vedremo (?:più avanti|dopo|tra poco)"
    # «Vediamo ora…», «vediamo come…» announce; «lo vediamo nei progetti» and
    # «il pattern che vediamo funzionare» report experience and are not counted.
    r"|vediamo(?:lo|li|la)? (?:ora|adesso|insieme|nel dettaglio|meglio|perché|come|cosa|quali|quando)\b|^vediamo\b"
    r"|riassumendo|ricapitolando|in sintesi|in conclusione|per concludere|tirando le somme"
    r"|detto questo|ciò detto|premesso (?:questo|ciò)|andiamo con ordine|mettiamola così"
    r"|il punto (?:è|qui è|vero è|centrale è)|la tesi (?:di questo|è|qui è)"
    r"|la (?:vera )?domanda (?:è|sorge|resta|rimane)|resta (?:però )?una domanda"
    r"|lo diciamo (?:subito|chiaramente|senza giri)|diciamolo(?: subito| chiaramente)?"
    r"|va detto|va precisato|va chiarito|un chiarimento (?:serve|è d'obbligo|è necessario)"
    r"|a scanso di equivoci|per dirla tutta|per capirci|per intenderci|detto (?:senza|in altre parole)"
    r"|facciamo un passo indietro|torniamo (?:a noi|al punto|alla domanda)"
    r"|prima di (?:entrare nel merito|andare avanti|proseguire)|entriamo nel merito"
    r"|voce per voce|punto per punto"
    r"|(?:ed )?è qui che (?:entra|arriva|si gioca|sta)|^ecco (?:il|la|i|le|un|una|lo) (?:recap|riepilogo|punto|quadro|nodo|motivo)"
    # Announcing formulas: the sentence says that a statement is
    # coming instead of making it. «Va messo sul tavolo anche il contesto delle
    # licenze» carries no information that «Pesa anche la licenza» lacks.
    r"|va (?:messo sul tavolo|sciolto|riconosciuto|ricordato|sottolineato|aggiunto|considerato|tenuto presente|premesso)"
    r"|vale la pena (?:riconoscere|ricordare|notare|dire|chiarire|precisare|sottolineare|fermarsi|soffermarsi)"
    r"|tradotto in (?:pratica|termini|condizioni)|tradotto:|in pratica:"
    r"|un (?:equivoco|malinteso|fraintendimento) (?:diffuso |frequente |comune )?(?:va|da) (?:sciolto|chiarito|superato)"
    r"|(?:ed )?è proprio (?:questo|qui|questa) (?:il criterio|il punto|la ragione|il motivo|che)"
    r"|mettiamo (?:sul tavolo|in fila|in chiaro)|partiamo da|cominciamo (?:da|con)|conviene (?:chiarire|precisare|dirlo subito)"
    # A copula that announces what the colon is about to say («La regola è
    # semplice:», «la traduzione è diretta:», «Il filo conduttore è uno solo:»).
    # Only when the colon carries the statement: «…sono queste:» closing the
    # sentence introduces a list, an ordinary convention.
    r"|(?:è|sono) (?:semplice|semplici|diretta|diretto|chiara|chiaro|questa|questo|questi|queste|uno solo|una sola|duplice)\s*:(?=\s*\S)"
    r"|in parole (?:semplici|povere)|si riassume(?:re)? (?:così|in)|detto in altri termini"
    r"|quest[oa] (?:articolo|guida|post|testo) (?:si rivolge|parla|spiega|analizza|racconta|vuole)"
    r"|(?:di|in) quest[oa] (?:articolo|sezione|guida|capitolo)"
    r"|non troverai qui|ci torniamo|si chiude (?:il|un) (?:primo )?cerchio|il confronto che segue|griglia di lettura"
    r"|ne deriva (?:una|un|che)|tradott[oaie] in termini"
    r"|va(?:nno)? (?:dichiarat[oaie]|esplicitat[oaie]|mess[oaie] sul tavolo)|lo diciamo (?:apertamente|francamente)"
    r")",
    re.I,
)

_BRIDGE_PHRASE_RE = re.compile(
    r"^(?:"
    r"ed è (?:esattamente|proprio|precisamente) (?:qui|questo|quello|per questo)"
    r"|e allora(?: bisogna| serve| la domanda)?"
    r"|e qui (?:sta|viene|entra|arriva|nasce)"
    r"|da qui (?:parte|nasce|discende|la)"
    r"|la risposta (?:sta|è|arriva|passa)"
    r"|resta però|non regge|ecco perché|ed è per questo"
    r")\b",
    re.I,
)

_ANTITHESIS_RES = (
    re.compile(
        # «chi non è tecnico» is a relative clause, not a contrast.
        r"(?<!\bchi )\bnon (?:è|sono|era|erano|si tratta(?: di)?|significa|vuol dire|serve|basta|conta|importa)\b"
        r"[^.;:!?\n]{2,80}?(?:[:;]|,\s*(?:è|sono|significa|vuol dire|serve|conta|ma\b|bensì\b|quanto\b))",
        re.I,
    ),
    re.compile(r"\bnon (?:solo|soltanto|tanto)\b[^.;!?\n]{2,80}?\b(?:ma(?: anche)?|quanto|bensì)\b", re.I),
    re.compile(r"\bpiù che\b[^.;!?\n]{2,60}?\b(?:è|sono|si tratta|conta)\b", re.I),
    # «la norma, non l'eccezione», «su trimestri, non su sprint», «un punto di
    # partenza, non un traguardo»: the contrast is appended as a
    # negated tail of one to four words that closes the clause.
    re.compile(
        r",\s*non (?:un[oa']?|il|lo|la|i|gli|le|l'|su|di|del|della|dei|per|a|in|come|da)?\s*[\wà-ù'’]+(?:\s+[\wà-ù'’]+){0,6}\s*(?:[.;:!?]|$)",
        re.I,
    ),
    # A negated aside inside the clause: «…, non il tool, che riduce…».
    re.compile(r",\s*non (?:un[oa']?|il|lo|la|i|gli|le|l')\s*[\wà-ù'’]+(?:\s+[\wà-ù'’]+){0,2},", re.I),
    # «…e non un progetto a sé», «…e non una scelta».
    re.compile(r"\be non (?:un[oa']?|il|lo|la|i|gli|le|l')\s*[\wà-ù'’]+", re.I),
    # «una questione di continuità prima (ancora) che di architettura»,
    # «normativo oltre che architetturale», «smette di essere X e diventa Y».
    re.compile(r"\bprima (?:ancora )?che (?:di|da|per|a|in|nel|nella|della|del|dal|dalla)\b", re.I),
    re.compile(r"\boltre che\b", re.I),
    re.compile(r"\bsmette di essere\b[^.;!?\n]{2,80}?\be diventa\b", re.I),
)

#: The antithesis split across two sentences: «Le voci
#: di costo non sono i nodi. Sono le componenti laterali…», «Quel numero misura
#: quanto è diffusa. Non misura quanto è adatta.»
_NEGATED_COPULA_RE = re.compile(r"\bnon (?:è|sono|era|erano)\b|^nessun[oa]?\b", re.I)
_AFFIRMED_COPULA_RE = re.compile(r"^(?:è|sono|era|erano)\b", re.I)
_LEADING_NEGATION_RE = re.compile(r"^non ([a-zà-ù]{4,})\b", re.I)


@dataclass(frozen=True)
class TellHit:
    kind: str
    sentence: str


def _is_question(sentence: str) -> bool:
    return sentence.rstrip().endswith("?")


def _detect_meta(sentences: list[str]) -> list[TellHit]:
    return [TellHit("meta_discourse", s) for s in sentences if _META_DISCOURSE_RE.search(s)]


def _detect_bridges(sentences: list[str], *, has_next_paragraph: bool) -> list[TellHit]:
    hits: list[TellHit] = []
    for s in sentences:
        if _BRIDGE_PHRASE_RE.match(s.lstrip("\"“«(")):
            hits.append(TellHit("rhetorical_bridge", s))
    if sentences:
        last = sentences[-1]
        only_question = len(sentences) == 1 and _is_question(last)
        closing_question = len(sentences) > 1 and _is_question(last) and has_next_paragraph
        if (only_question or closing_question) and not any(h.sentence == last for h in hits):
            hits.append(TellHit("rhetorical_bridge", last))
    return hits


_DIGIT_RE = re.compile(r"\d")
_PROPER_NOUN_RE = re.compile(r"\b[A-ZÀÈÉÌÒÙ][a-zà-ù]+\b")
_COPULA_RE = re.compile(
    r"\b(?:è|sono|era|erano|resta|restano|conta|contano|serve|servono|basta|bastano|significa|vuol dire|vale)\b",
    re.I,
)
_ABSTRACT_OPENER_RE = re.compile(
    r"^(?:quest[oa]|quell[oa]|il punto|la differenza|il resto|il problema|la domanda|la risposta|il rischio"
    r"|il prezzo|il costo|la posta|la sfida|il nodo|la partita|non è|non era|non sono|è|sono|resta|conta"
    r"|serve|basta|ecco|tutto|niente|nulla|nessuno|nessuna|il contrario|l'opposto|punto|fine|stop)\b",
    re.I,
)


def _is_aphoristic(sentence: str, *, max_words: int) -> bool:
    """A short closing sentence that states an abstraction rather than a fact.

    No digits, no proper noun after the first word, a copula or an abstract
    opener: «Il resto è dettaglio.», «Non è un problema tecnico.», «Questo
    conta.» A short factual close («Il progetto è nato nel 2015.», «Lo usa
    anche Netflix.») is not counted: good writers close on facts too.
    """

    body = sentence.strip().lstrip("\"“«(")
    if _is_question(body) or body.rstrip().endswith(":"):
        return False
    n = count_words(body)
    if n < 2 or n > max_words:
        return False
    if _DIGIT_RE.search(body):
        return False
    if _PROPER_NOUN_RE.search(body[1:]):
        return False
    return bool(_COPULA_RE.search(body) or _ABSTRACT_OPENER_RE.match(body))


def _detect_punch(sentences: list[str], *, max_words: int) -> list[TellHit]:
    """The «build-build-punch» cadence: an aphoristic short sentence that closes
    a paragraph, stands alone as one, or sits mid-paragraph as a sententious
    beat («Il meccanismo è semplice.»). Short openings are not
    counted: good writers open on a short sentence too."""

    if not sentences:
        return []
    if len(sentences) == 1:
        return [TellHit("punch_sentence", sentences[0])] if _is_aphoristic(sentences[0], max_words=max_words) else []
    return [
        TellHit("punch_sentence", s)
        for s in sentences[1:]
        if _is_aphoristic(s, max_words=max_words)
    ]


def _detect_antithesis(sentences: list[str]) -> list[TellHit]:
    hits = [
        TellHit("antithesis", s)
        for s in sentences
        if any(rx.search(s) for rx in _ANTITHESIS_RES)
    ]
    counted = {h.sentence for h in hits}
    for first, second in zip(sentences, sentences[1:]):
        if second in counted or first in counted:
            continue
        a, b = first.strip().lstrip("\"“«("), second.strip().lstrip("\"“«(")
        split = bool(_NEGATED_COPULA_RE.search(a) and _AFFIRMED_COPULA_RE.match(b))
        if not split:
            m = _LEADING_NEGATION_RE.match(b)
            split = bool(m and re.search(rf"\b{re.escape(m.group(1))}\b", a, re.I))
        if split:
            hits.append(TellHit("antithesis", second))
            counted.add(second)
    return hits


#: A colon that hooks an explanation to the clause before it («il risultato:
#: un cluster inutile»). Times (12:30), URLs and a colon that introduces a
#: quotation or a list are not counted. The sentence splitter breaks on the
#: colon itself, so the detector reads the paragraph, not the sentences.
_COLON_CHAIN_RE = re.compile(r"(?<!\d)(?<!https)(?<!http):\s+(?=[a-zà-ù])")
#: Three items in a row joined by a final «e»: «veloce, sicuro e scalabile»,
#: «processi, persone e strumenti». One to three words per item, all lower
#: case: a list of proper nouns («Roma, Milano e Torino») is information,
#: not cadence, and is not counted.
#: Three SINGLE words in a row, with nothing before the first comma that
#: would make it a longer list or a phrase: «flessibilità, scalabilità e
#: sicurezza», «configurare, estendere e personalizzare», «pubblico,
#: ispezionabile e modificabile». The first version took multi-word items and
#: let an item start mid-phrase («tre lingue, quindici redattori e un…»), so
#: it counted ordinary lists of facts as cadence.
_TRIAD_RE = re.compile(
    r"(?<![\wà-ù'’])([a-zà-ù]{4,}), ([a-zà-ù]{4,}) e ([a-zà-ù]{4,})(?=\s*(?:[.,;:!?)]|$))"
)
#: A comma and a word right before the first item: the triad is the tail of a
#: longer list, which is information, not cadence.
_LONGER_LIST_RE = re.compile(r"[\wà-ù'’]+,\s*$")
_TRIAD_FUNCTION_WORDS = frozenset(
    "come anche quando dove mentre perché quindi oppure ovvero cioè ogni altri altre altro altra "
    "sono essere avere hanno sulla sulle dalla dalle nella nelle della delle degli questo questa "
    "questi queste quello quella quelli quelle loro tutti tutte molto poco sempre ancora".split()
)
_TERMINAL_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _detect_colon_chain(paragraph: str) -> list[TellHit]:
    """One hit per terminal sentence that chains an explanation with a colon."""

    hits: list[TellHit] = []
    for segment in _TERMINAL_SPLIT_RE.split(paragraph):
        if segment.rstrip().endswith(":"):
            continue  # introduces what follows (a list, a quotation): not a chain
        if _COLON_CHAIN_RE.search(segment):
            hits.append(TellHit("colon_chain", segment.strip()))
    return hits


def _detect_triad(paragraph: str) -> list[TellHit]:
    """One hit per terminal sentence that carries an «X, Y e Z» triad of single words."""

    hits: list[TellHit] = []
    for segment in _TERMINAL_SPLIT_RE.split(paragraph):
        for m in _TRIAD_RE.finditer(segment):
            if any(w in _TRIAD_FUNCTION_WORDS for w in m.groups()):
                continue
            if _LONGER_LIST_RE.search(segment[: m.start()]):
                continue
            hits.append(TellHit("triad", segment.strip()))
            break
    return hits


def _rhythm(paragraphs: list[ProseParagraph], word_count: int) -> dict[str, "RhythmMeasure"]:
    """The two document-level rhythm measures against the human floor."""

    lengths = [
        count_words(seg)
        for p in paragraphs
        for seg in _TERMINAL_SPLIT_RE.split(p.text)
        if count_words(seg) > 0
    ]
    cv = 0.0
    if len(lengths) > 1:
        mean = sum(lengths) / len(lengths)
        var = sum((x - mean) ** 2 for x in lengths) / len(lengths)
        cv = (var ** 0.5) / mean if mean else 0.0
    parens = sum(p.text.count("(") for p in paragraphs)
    per_1000 = parens * 1000 / word_count if word_count else 0.0
    out: dict[str, RhythmMeasure] = {}
    for kind, value in (("sentence_length_cv", round(cv, 2)), ("parentheses", round(per_1000, 1))):
        norm = RHYTHM_NORM[kind]
        out[kind] = RhythmMeasure(
            kind=kind,
            value=value,
            p10=norm.p10,
            median=norm.median,
            below=value < norm.p10 and word_count >= 300,
        )
    return out


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StyleMeasure:
    kind: str
    enabled: bool
    count: int
    per_1000: float
    threshold: float
    median: float
    p90: float

    @property
    def above(self) -> bool:
        return self.enabled and self.per_1000 > self.threshold


@dataclass(frozen=True)
class FlaggedParagraph:
    """A prose paragraph that contributes to at least one tell above the norm."""

    paragraph: ProseParagraph
    tells: tuple[str, ...]
    hits: tuple[TellHit, ...]
    finding_id: str


@dataclass(frozen=True)
class RhythmMeasure:
    """A document-level rhythm measure against the human floor (10th percentile)."""

    kind: str
    value: float
    p10: float
    median: float
    below: bool

    @property
    def label(self) -> str:
        return RHYTHM_LABELS_IT[self.kind]

    @property
    def description(self) -> str:
        return RHYTHM_DESCRIPTIONS_IT[self.kind]


@dataclass(frozen=True)
class StyleMeasurement:
    word_count: int
    paragraph_count: int
    measures: dict[str, StyleMeasure]
    flagged: tuple[FlaggedParagraph, ...]
    #: Rhythm measures; empty when disabled.
    rhythm: dict[str, RhythmMeasure] = field(default_factory=dict)

    @property
    def within_norm(self) -> bool:
        return not any(m.above for m in self.measures.values())

    @property
    def tells_above(self) -> tuple[str, ...]:
        return tuple(k for k in TELL_KINDS if k in self.measures and self.measures[k].above)

    def rates(self) -> dict[str, float]:
        return {k: m.per_1000 for k, m in self.measures.items()}


def normalise_paragraph(text: str) -> str:
    """Lowercase, strip accents' variants of apostrophes, collapse whitespace, drop punctuation.

    A punctuation-only edit keeps the finding identity; a rewrite changes it.
    """

    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


@dataclass(frozen=True)
class PhraseHit:
    """A prose paragraph that contains at least one of the given phrases."""

    paragraph: ProseParagraph
    phrases: tuple[str, ...]
    #: A verbatim slice of the source markdown that anchors the paragraph:
    #: the first sentence carrying a phrase, else the start of the block.
    excerpt: str


def find_phrases(markdown: str, phrases: Iterable[str], *, max_chars: int = 400) -> list[PhraseHit]:
    """Locate case-insensitive phrases in the prose paragraphs of ``markdown``.


    Args:
        markdown: The article body.
        phrases: Phrases to look for (the slop scan's matched texts).
        max_chars: Cap on the excerpt length.

    Returns:
        One hit per paragraph, in document order, with the phrases it holds.
    """

    wanted = [ph for ph in dict.fromkeys((ph or "").strip() for ph in phrases) if ph]
    if not wanted:
        return []
    hits: list[PhraseHit] = []
    for paragraph in extract_prose(markdown):
        lowered = paragraph.text.lower()
        present = tuple(ph for ph in wanted if ph.lower() in lowered)
        if not present:
            continue
        block = markdown[paragraph.start : paragraph.end]
        excerpt = block.strip()[:max_chars]
        for sentence in split_sentences(paragraph.text):
            probe = sentence.strip()
            if probe and probe in block and any(ph.lower() in probe.lower() for ph in present):
                excerpt = probe[:max_chars]
                break
        hits.append(PhraseHit(paragraph=paragraph, phrases=present, excerpt=excerpt))
    return hits


def style_finding_id(kinds: Iterable[str], paragraph_text: str) -> str:
    basis = "style_tells|" + ",".join(sorted(set(kinds))) + "|" + normalise_paragraph(paragraph_text)
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def measure(markdown: str, settings: Optional[StyleMeterSettings] = None) -> StyleMeasurement:
    """Measure the six tells and the two rhythm measures on the prose of ``markdown``.

    Args:
        markdown: Article body in Markdown.
        settings: Thresholds, toggles and the punch word limit.

    Returns:
        Rates per 1000 prose words, the comparison with the norm, and the
        paragraphs that contribute to any tell above its threshold.
    """

    settings = settings or StyleMeterSettings()
    paragraphs = extract_prose(markdown)
    word_count = sum(count_words(p.text) for p in paragraphs)

    per_paragraph: list[list[TellHit]] = []
    for i, p in enumerate(paragraphs):
        sentences = split_sentences(p.text)
        hits: list[TellHit] = []
        hits += _detect_meta(sentences)
        hits += _detect_bridges(sentences, has_next_paragraph=i < len(paragraphs) - 1)
        hits += _detect_punch(sentences, max_words=settings.punch_max_words)
        hits += _detect_antithesis(sentences)
        hits += _detect_colon_chain(p.text)
        hits += _detect_triad(p.text)
        per_paragraph.append(hits)

    measures: dict[str, StyleMeasure] = {}
    for kind in TELL_KINDS:
        count = sum(1 for hits in per_paragraph for h in hits if h.kind == kind)
        rate = round(count * 1000 / word_count, 1) if word_count else 0.0
        norm = HUMAN_NORM[kind]
        measures[kind] = StyleMeasure(
            kind=kind,
            enabled=kind in settings.enabled,
            count=count,
            per_1000=rate,
            threshold=settings.threshold_for(kind),
            median=norm.median,
            p90=norm.p90,
        )

    above = {k for k, m in measures.items() if m.above}
    flagged: list[FlaggedParagraph] = []
    if above:
        for p, hits in zip(paragraphs, per_paragraph):
            relevant = tuple(h for h in hits if h.kind in above)
            if not relevant:
                continue
            kinds = tuple(k for k in TELL_KINDS if any(h.kind == k for h in relevant))
            flagged.append(
                FlaggedParagraph(
                    paragraph=p,
                    tells=kinds,
                    hits=relevant,
                    finding_id=style_finding_id(kinds, p.text),
                )
            )

    return StyleMeasurement(
        word_count=word_count,
        paragraph_count=len(paragraphs),
        measures=measures,
        flagged=tuple(flagged),
        rhythm=_rhythm(paragraphs, word_count) if settings.rhythm_enabled else {},
    )


def verbatim_excerpt(markdown: str, flagged: FlaggedParagraph, *, max_chars: int = 400) -> str:
    """A slice of the ORIGINAL markdown that anchors the finding.

    Findings are matched back to the draft by verbatim excerpt (whitespace
    folded, case folded), so the excerpt must exist byte-for-byte in the
    markdown, not in the plain-text view the meter measured. Preference: the
    first offending sentence as written in the source; fallback: the start of
    the paragraph's own block.
    """

    block = markdown[flagged.paragraph.start : flagged.paragraph.end]
    for hit in flagged.hits:
        probe = hit.sentence.strip()
        if probe and probe in block:
            return probe[:max_chars]
        # Emphasis or a link inside the sentence: try its first words.
        words = probe.split()
        for n in (8, 6, 4):
            head = " ".join(words[:n])
            if len(words) >= n and head in block:
                idx = block.find(head)
                end = block.find(".", idx)
                return block[idx : (end + 1 if end != -1 else idx + max_chars)][:max_chars]
    return block.strip()[:max_chars]


def format_rate_it(value: float) -> str:
    """1 decimal, Italian comma."""

    return f"{value:.1f}".replace(".", ",")
