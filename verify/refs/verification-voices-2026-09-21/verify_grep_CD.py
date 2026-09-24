import re, html, subprocess, os
A = lambda i: f"https://arxiv.org/abs/{i}"
targets = {
 # ---- agent C
 "ax_2609_05505": (A("2609.05505"), ["only 30%", "25% of limitations", "0.97", "0.37", "22 open-weight"]),
 "ax_2605_06635": (A("2605.06635"), ["above 94%", "above 80%", "39-77%", "approximately 42%", "2 to 150"]),
 "ax_2606_07951": (A("2606.07951"), ["75%", "1.5", "20%", "40%", "five iterations", "epistemic faithfulness"]),
 "ax_2602_10881": (A("2602.10881"), ["near-zero reliability", "numeric misattribution", "role reversal", "binding drift"]),
 "ax_2607_20527": (A("2607.20527"), ["3%", "18%", "0.27", "0.94", "conformal", "PaperQA2"]),
 "ax_2608_26885": (A("2608.26885"), ["91.7%", "94 records", "29 verified eligible", "No workflow recovered all", "83.9%", "82.3"]),
 "ax_2605_20668": (A("2605.20668"), ["45 domain scientists", "469 hours", "2,960", "82 Nature", "60.0%", "48.2%", "21%", "3%", "26%"]),
 "ax_2604_01128": (A("2604.01128"), ["more than 10 hallucinations", "51 papers", "Codex"]),
 "ax_2607_00738": (A("2607.00738"), ["one in twenty", "identity-level", "below 1%", "$0.04"]),
 "ax_2602_05867": (A("2602.05867"), ["2-6%", "none of the 2021", "four major high-performance computing"]),
 "ax_2602_06718": (A("2602.06718"), ["14.23%", "94.93%", "1.07%", "80.9%", "56,381", "76.7%"]),
 "ax_2602_05930": (A("2602.05930"), ["66%", "53 published papers", "27%", "100%", "63%", "3-5 expert"]),
 "ax_2605_07723": (A("2605.07723"), ["111 million", "146,932", "2.5 million papers", "arXiv, bioRxiv, SSRN"]),
 "ax_2603_20235": (A("2603.20235"), ["20%", "bias of ignorance", "sycophancy", "paradox"]),
 "ax_2608_12741": (A("2608.12741"), ["82.8%", "91.8%", "244", "cross-source synthesis"]),
 "ax_2606_19749": (A("2606.19749"), ["71.6%", "83.3%", "83.0%", "1.44"]),
 "ax_2603_05912": (A("2603.05912"), ["60.8%", "90.9%", "Audit-then-Score", "four"]),
 "ax_2606_19544": (A("2606.19544"), ["33", "41", "541,000", "14 positions", "Minimum Viable Validation"]),
 "ax_2604_03159": (A("2604.03159"), ["83.6%", "91.5%", "50.9%", "78.3%", "27.7", "931"]),
 "ax_2607_09932": (A("2607.09932"), ["1.55", "Unsupported Claims", "1,800"]),
 "ax_2606_32029": (A("2606.32029"), ["12.0%", "78.2%", "1.7B to 20B"]),
 "ax_2604_25256": (A("2604.25256"), ["9.39%", "9.31%", "Wide Research"]),
 "ax_2604_18880": (A("2604.18880"), ["108,000", "author names", "Author names"]),
 "ax_2603_22344": (A("2603.22344"), ["47.8%", "2,000 references", "40 randomly"]),
 "ax_2602_23452": (A("2602.23452"), ["97.3%", "97.2%", "6,475", "GPTZero"]),
 "ax_2605_08583": (A("2605.08583"), ["97.1%", "957", "ICLR 2026", "12"]),
 "ax_2605_27700": (A("2605.27700"), ["88.7%", "88.9%", "982"]),
 "frontiers_oami": ("https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2026.1799623/full", ["67", "93%", "0.7", "14%", "Missing Data", "Fabricated"]),
 "gptzero_neurips": ("https://gptzero.me/news/neurips/", ["4841", "100 confirmed", "51 NeurIPS", "vibe citing"]),
 "gptzero_ey": ("https://gptzero.me/investigations/ey", ["16 of 27", "16 out of 27", "citations on faith", "manually verified"]),
 # ---- agent D
 "ax_2608_01000": (A("2608.01000"), ["6-7x", "10:1", "58-92%", "5-39%", "authoring problem itself", "judge whether a candidate"]),
 "ax_2605_29800": (A("2605.29800"), ["9 frontier LLMs", "2 independent votes", "8-22", "11%", "best single judge"]),
 "ax_2606_29920": (A("2606.29920"), ["2,458", "substantial noise", "diminishing returns"]),
 "ax_2606_26300": (A("2606.26300"), ["being inverted", "only a proxy for human intent", "co-evolve"]),
 "ax_2605_12947": (A("2605.12947"), ["release decision", "hard-negative", "e-process"]),
 "anthropic_evals": ("https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents", ["Coverage checks define key facts", "closely calibrated with human experts", "Unknown", "Read the transcripts", "Jan 9, 2026|January 9, 2026|2026-01-09"]),
 "eugene_yan": ("https://eugeneyan.com/writing/working-with-ai/", ["verification as a ladder", "models watch models", "Shift verification left", "May 2026"]),
 "hamel_faq": ("https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html", ["at least 30 traces", "roughly 100 diverse traces", "theoretical saturation", "2026"]),
 "pmc_dualllm": ("https://pmc.ncbi.nlm.nih.gov/articles/PMC13418397/", ["315 (82%)", "365 (95.1%)", "omission of minor details", "automation bias", "2026"]),
 "elicit_solutions": ("https://elicit.com/solutions/systematic-review", ["exact sentence or figure", "PRISMA-auditable", "99.5%"]),
 "charlotin": ("https://www.damiencharlotin.com/hallucinations/", ["2,046", "2046", "tracks legal"]),
 "karpathy_sequoia": ("https://karpathy.bearblog.dev/sequoia-ascent-2026/", ["Traditional computers automate", "council of LLM judges", "verification rewards", "almost everything can be made verifiable"]),
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
    # for arxiv abs pages, restrict to abstract block if present
    m = re.search(r"Abstract:(.*?)(Comments:|Subjects:|Cite as:)", txt)
    scope = m.group(1) if (name.startswith("ax_") and m) else txt
    dm = re.search(r"\[Submitted on ([^\]]+)\]", txt)
    out.append(f"\n===== {name} | {url} | bytes={len(raw)} textlen={len(txt)} | submitted={dm.group(1) if dm else '-'}")
    for ph in phrases:
        pat = ph if "|" in ph else re.escape(ph)
        idxs=[m.start() for m in re.finditer(pat, scope, flags=re.I)]
        if not idxs: out.append(f"  [ABSENT] {ph!r}")
        else:
            i=idxs[0]; s=max(0,i-160); e=min(len(scope), i+len(ph)+160)
            out.append(f"  [HIT x{len(idxs)}] {ph!r}\n     ...{scope[s:e]}...")
open("verify_CD_out.txt","w").write("\n".join(out))
print(len("\n".join(out)))
