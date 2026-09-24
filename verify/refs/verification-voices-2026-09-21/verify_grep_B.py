import re, html, subprocess, os
targets = {
 "anthropic_science": ("https://www.anthropic.com/news/claude-science-ai-workbench", ["reviewer agent", "actor-critic", "evidence state database", "full message history", "flagging incorrect citations"]),
 "elicit_slr": ("https://elicit.com/blog/evaluating-elicit-slr", ["95.0%", "99.5%", "95.6%", "994", "38,493", "randomly selected 25", "open-access"]),
 "arxiv_2604_03173": ("https://arxiv.org/abs/2604.03173", ["3--13%", "3-13%", "6--79", "6-79", "Wayback", "53,090"]),
 "arxiv_2604_13940": ("https://arxiv.org/html/2604.13940v1", ["22,977", "1356", "1346", "randomly sampled 100 reviews", "peer reviews of peer reviews"]),
 "neurips_blog": ("https://blog.neurips.cc/2026/06/02/ai-generated-papers-in-the-neurips-2026-position-paper-track/", ["version history", "178 submissions", "18.4%", "123 submissions", "substantially written by human"]),
 "dm_conjecture": ("https://deepmind.google/public-policy/conjecture-machines-ai-agents-and-the-new-validation-bottleneck-in-science/", ["conjecture machines", "Refutations remain physical", "proof indigestion", "Interaction Cards"]),
 "dm_coscientist": ("https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/", ["virtual peer reviewer", "majority of the system", "cross-checking claims"]),
 "pmc_kalai": ("https://pmc.ncbi.nlm.nih.gov/articles/PMC13216060/", ["guessing is a dominant strategy", "open rubrics", "lacking repeated support", "4,326"]),
 "sn_guidance": ("https://group.springernature.com/gp/group/ai/ai-guidance-for-our-researchers-and-communities", ["verify the accuracy and authenticity", "fabricated or outdated references", "cannot replace reviewer expertise", "tool versions, usage dates, prompts"]),
 "icmje": ("https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html", ["authoritative-sounding", "appropriate attribution of all quoted material", "cannot be responsible for the accuracy"]),
 "arxiv_2607_22693": ("https://arxiv.org/abs/2607.22693", ["CheckIfExist", "reference extraction errors", "multi-source"]),
 "arxiv_2603_19236": ("https://arxiv.org/abs/2603.19236", ["statistical pre-screening", "non-determinism"]),
 "retractionwatch": ("https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/", ["4,406", "4,046", "97.1 million", "2,828", "458", "277", "2,810"]),
 "thescientist": ("https://www.the-scientist.com/one-in-277-biomedical-papers-carry-fake-references-74480", ["4,046", "4,406", "125.6 million", "2,828", "2,810", "56.9"]),
 "statnews": ("https://www.statnews.com/2026/05/07/lancet-study-finds-steep-rise-fraudulent-citations-academic-papers/", ["2,828", "458", "277", "97 million", "4,000", "automated tool to check references", "two publishers"]),
 "tao_openai_forum": ("https://forum.openai.com/public/blogs/terence-tao-ai-is-ready-for-primetime-in-math-and-theoretical-physics-2026-03-10", ["hiding the weak step", "reliable verification of proofs", "literature search"]),
 "aisi_dyl": ("https://www.aisi.gov.uk/research/did-you-lie-evaluating-lie-detectors-across-model-scale-and-belief-verified-model-organisms", ["0.82", "chain-of-thought judge"]),
 "lancet_primary": ("https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00603-3/fulltext", ["2,828", "277", "fabricated"]),
 "lancet_editorial": ("https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00798-1/abstract", ["91%", "fabricated"]),
}
def fetch(url, name):
    p = f"pages/{name}.html"
    if not os.path.exists(p) or os.path.getsize(p) < 500:
        subprocess.run(["curl","-sL","--max-time","40","-A","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",url,"-o",p], capture_output=True)
    return open(p, errors="replace").read() if os.path.exists(p) else ""
def totext(h):
    h = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h))
out=[]
for name,(url,phrases) in targets.items():
    raw = fetch(url,name); txt = totext(raw)
    out.append(f"\n===== {name} | {url} | bytes={len(raw)} textlen={len(txt)}")
    for ph in phrases:
        idxs=[m.start() for m in re.finditer(re.escape(ph), txt, flags=re.I)]
        if not idxs: out.append(f"  [ABSENT] {ph!r}")
        else:
            for i in idxs[:2]:
                s=max(0,i-200); e=min(len(txt), i+len(ph)+200)
                out.append(f"  [HIT x{len(idxs)}] {ph!r}\n     ...{txt[s:e]}...")
open("verify_B_out.txt","w").write("\n".join(out))
print("\n".join(out)[:200])
