"""Shared formatting utilities — boxify, duration, etc."""


def boxify(body: str, title: str = "🤖 KAOS") -> str:
    lines = body.strip().split("\n")
    w = max(len(l) for l in lines) + 2
    top = "╔" + "═" * (w + 2) + "╗"
    hdr = "║ " + title.ljust(w) + " ║"
    sep = "╠" + "═" * (w + 2) + "╣"
    body_lines = "\n".join("║ " + l.ljust(w) + " ║" for l in lines)
    bot = "╚" + "═" * (w + 2) + "╝"
    return f"`{top}\n{hdr}\n{sep}\n{body_lines}\n{bot}`"


def fmt_duration(s: int) -> str:
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
