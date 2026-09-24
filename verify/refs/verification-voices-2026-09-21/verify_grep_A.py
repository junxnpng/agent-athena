import re, html, subprocess, sys, json, hashlib, os
targets = {
 "karpathy_sequoia": ("https://karpathy.bearblog.dev/sequoia-ascent-2026/", ["automates what you can", "does not blindly accept generated code", "remain jagged", "aesthetics, judgment, taste"]),
 "tao_icm": ("https://arxiv.org/html/2608.16753v1", ["clear, expert-level talk", "no longer depends on the reputation", "not even the humans who prompted", "disclosing tool use", "verification", "digest"]),
 "tao_palomar": ("https://terrytao.wordpress.com/2026/08/18/palomar-a-registry-of-lean-verified-mathematics/", ["proliferation of AI-generated proofs", "somewhat non-trivial", "not a peer-reviewed journal", "fall well short"]),
 "tao_aiviews": ("https://teorth.github.io/tao-web/ai-views.html", ["Achilles heel", "independently verify their output", "job description"]),
 "willison_meat": ("https://simonwillison.net/2026/Aug/3/dont-be-a-meat-proxy/", ["meat proxy", "Read it, understand it, validate it"]),
 "willison_review": ("https://simonwillison.net/2026/Aug/22/more-than-just-code-review/", ["confidently verify that those changes", "Eyeballing every line"]),
 "weng_harness": ("https://lilianweng.github.io/posts/2026-07-04-harness/", ["Chain-of-Evidence", "plausible manuscript", "move up the stack"]),
 "buzzard_flt": ("https://xenaproject.wordpress.com/2026/09/04/flt-anthropic-has-beaten-me-to-it/", ["comparator on it", "100 or so lines", "tells us essentially nothing", "adds nothing"]),
 "gowers": ("https://gowers.wordpress.com/2026/08/12/what-sort-of-maths-are-llms-good-at/", ["not all that novel", "deep thought"]),
 "neurips26_ws": ("https://ai4sciencecommunity.github.io/neurips26", ["no longer hypothesis generation", "scarce verification budget"]),
 "hamel_smell": ("https://hamelhusain.substack.com/p/its-hard-to-eval-is-a-product-smell", ["hard for users too", "common thread across these examples is provenance"]),
 "hamel_autoeval": ("https://hamelhusain.substack.com/p/do-automated-evals-work", ["87 percent", "looked correct", "issues humans missed"]),
 "shreya_qual": ("https://www.sh-reya.com/blog/ai-qual-analysis/", ["comparisons, over pairs of codes", "Vague codes", "provenance from category back to evidence"]),
 "ng_batch": ("https://www.deeplearning.ai/the-batch/three-key-loops-for-building-great-software", ["until the code is bug-free", "context advantage", "human-in-the-loop is needed"]),
 "mollick_overhang": ("https://www.oneusefulthing.org/p/the-overhang", ["which AI outputs to keep", "Zork"]),
 "cacm_rao": ("https://cacm.acm.org/news/thats-logical-teaching-llms-to-give-better-answers/", ["do it alone", "verifier"]),
 "raschka_effort": ("https://magazine.sebastianraschka.com/p/controlling-reasoning-effort-in-llms", ["Only the final answer and response format determine the reward", "do not make the model reason"]),
 "marcus_0612": ("https://garymarcus.substack.com/p/you-cant-get-more-2026-than-that", ["no longer have to check", "assumption that you", "check it"]),
 "marcus_slop": ("https://garymarcus.substack.com/p/slop-productivity-and-why-the-ai", ["plausible but unreliable", "difficult to distinguish from correct"]),
 "lawzero": ("https://lawzero.org/en/research", ["transparent, auditable and verifiable"]),
 "spectrum_tao": ("https://spectrum.ieee.org/ai-in-mathematics", ["formal verification layer", "filters out a lot of the rubbish"]),
 "dwarkesh_tao": ("https://www.dwarkesh.com/p/terence-tao", ["thousands of theories", "backdoors"]),
 "amodei_pace": ("https://darioamodei.com/post/we-must-pace-the-frontier", ["employee-level access", "nuts and bolts"]),
 "anthropic_flt": ("https://www.anthropic.com/research/formalizing-fermats-last-theorem", ["rigorously check LLM-generated mathematics"]),
}
def fetch(url, name):
    p = f"pages/{name}.html"
    if not os.path.exists(p) or os.path.getsize(p) < 500:
        r = subprocess.run(["curl","-sL","--max-time","40","-A","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",url,"-o",p], capture_output=True)
    return open(p, errors="replace").read() if os.path.exists(p) else ""
def totext(h):
    h = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    return re.sub(r"\s+", " ", h)
out=[]
for name,(url,phrases) in targets.items():
    raw = fetch(url,name)
    txt = totext(raw)
    out.append(f"\n===== {name} | {url} | bytes={len(raw)} textlen={len(txt)}")
    for ph in phrases:
        idxs=[m.start() for m in re.finditer(re.escape(ph), txt, flags=re.I)]
        if not idxs:
            out.append(f"  [ABSENT] {ph!r}")
        else:
            for i in idxs[:2]:
                s=max(0,i-220); e=min(len(txt), i+len(ph)+220)
                out.append(f"  [HIT x{len(idxs)}] {ph!r}\n     ...{txt[s:e]}...")
print("\n".join(out))
