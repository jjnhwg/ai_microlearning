import re

# default single-token fillers; caller can override
DEFAULT_FILLERS = frozenset({
    "um", "uh", "er", "erm", "ah", "hmm", "mhm",
    "like", "so", "actually", "basically", "literally", "right",
})

_STRIP = re.compile(r"[^\w']+")


def _normalize(word: str) -> str:
    """Lowercase and strip surrounding punctuation so 'Um,' matches 'um'."""
    return _STRIP.sub("", word.lower())


def count_fillers(words: list[dict], fillers: frozenset[str] = DEFAULT_FILLERS) -> dict:
    """Count filler words in a transcript's word list.

    words: list of {word, start, end, confidence} from transcribe().
    Returns total count, rate per minute, and each occurrence with its timing.
    """
    occurrences = []
    for w in words:
        if _normalize(w["word"]) in fillers:
            occurrences.append({
                "word": w["word"].strip(),
                "start": w["start"],
                "end": w["end"],
            })

    # speech span = last spoken word end - first spoken word start
    if words:
        span_seconds = words[-1]["end"] - words[0]["start"]
    else:
        span_seconds = 0.0
    minutes = span_seconds / 60.0

    rate_per_min = round(len(occurrences) / minutes, 2) if minutes > 0 else 0.0

    return {
        "count": len(occurrences),
        "rate_per_min": rate_per_min,
        "occurrences": occurrences,
    }


def words_per_minute(words: list[dict], window_s: float = 15.0, step_s: float = 5.0) -> dict:
    """Words-per-minute overall and over sliding windows.

    words: list of {word, start, end, ...} from transcribe().
    window_s: length of each sliding window in seconds.
    step_s: how far the window advances each step in seconds.
    Returns overall WPM plus a per-window pace curve (each tagged with its time range).
    """
    if not words:
        return {"overall_wpm": 0.0, "windows": []}

    speech_start = words[0]["start"]
    speech_end = words[-1]["end"]
    span_minutes = (speech_end - speech_start) / 60.0
    overall_wpm = round(len(words) / span_minutes, 1) if span_minutes > 0 else 0.0

    # a word counts toward a window if its midpoint falls inside it
    midpoints = [(w["start"] + w["end"]) / 2.0 for w in words]

    windows = []
    win_start = speech_start
    while win_start < speech_end:
        win_end = win_start + window_s
        in_window = sum(1 for m in midpoints if win_start <= m < win_end)
        wpm = round(in_window / (window_s / 60.0), 1)
        windows.append({
            "start": round(win_start, 3),
            "end": round(win_end, 3),
            "words": in_window,
            "wpm": wpm,
        })
        win_start += step_s

    return {"overall_wpm": overall_wpm, "windows": windows}


# def find_pauses(words: list[dict], min_pause_s: float = 0.5) -> dict:
    """Detect silent gaps between consecutive words.

    words: list of {word, start, end, ...} from transcribe().
    min_pause_s: minimum gap (seconds) to count as a pause; shorter gaps are ignored.
    Returns pause count, total silent duration, and each pause with its timing.
    Neutral measurement only — no good/bad judgment.
    """
    pauses = []
    for prev, curr in zip(words, words[1:]):
        gap = curr["start"] - prev["end"]
        if gap >= min_pause_s:
            pauses.append({
                "start": round(prev["end"], 3),
                "end": round(curr["start"], 3),
                "duration": round(gap, 3),
            })

    total_duration = round(sum(p["duration"] for p in pauses), 3)

    return {
        "count": len(pauses),
        "total_duration": total_duration,
        "pauses": pauses,
    }
