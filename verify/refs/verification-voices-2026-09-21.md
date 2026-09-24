# AI에 맡긴 논리 작업의 검증 — 2026년의 발언·기관·실증 (2026-09-21)

> **위치 (2026-09-22 이전).** `/work/jun/AI-helper/verify/`(jun-heo/AI-helper) 기준 상대 경로. `$KVCPOOL`=`/work/jun/priv-mb-eval/kvcpool-trace-gen`은 입력 데이터가 남아 있는 원 저장소다.

「40편을 읽고 KV 캐시 특성에 관한 문헌을 다 찾아 정리해 달라」는 식의 논리 작업을 AI에 맡겼을 때, 그 결과가 맞는지 어떻게 검증하는가. 2026년에 나온 발언·기관 실천·실증 연구를 웹에서 모으고, 인용은 원문에서 문자열로 대조한 기록이다. 학술 방법론(2021–2025) 정리는 [`verification-methods-2026-09-21.md`](verification-methods-2026-09-21.md)에 있고, 이 문서는 그 짝으로 2026년 자료만 다룬다.

## 0. 방법

- **조사.** Opus 에이전트 넷이 갈래를 나눠 웹 조사를 했다. A: 유명인의 2026년 발언. B: 연구소·연구 도구·출판사·학회의 2026년 실천. C: 2026년 실증 연구(오류율·검출기 성능). D: 실무자 방법과 실패 사례. 보고서 원문은 [`verification-voices-2026-09-21/`](verification-voices-2026-09-21/)의 `agent_A_voices.md`, `agent_B_institutions.md`, `agent_C_studies.md`, `agent_D_methods.md`.
- **검증.** Fable(이 문서의 작성자)이 보고서가 인용한 페이지를 curl로 받아 HTML을 벗긴 뒤, 인용 구절을 문자열로 grep했다(arXiv는 초록 블록 안에서만). JS 렌더링 페이지(Mastodon, Dwarkesh, The Scientist)는 WebFetch로 열었고, Lancet 서지는 Europe PMC REST로 확인했다. 장부는 같은 폴더의 `verify_A_grep.txt`, `verify_B_grep.txt`, `verify_CD_grep.txt`와 스크립트 `verify_grep_*.py`.
- **표기.** 영어 인용은 원문 문자열 그대로이고 정본이다. 바로 뒤 「」 안의 한글은 작성자의 번역이며, 원문의 강조·오타(예: Ng 글의 「to to」)는 번역에 옮기지 않았다.
- **열 수 없었던 곳.** X/Twitter(402/403), thelancet.com(403), openai.com(403), nature.com(IdP 리다이렉트), cacm.acm.org(403), sciencedirect.com(403). 이 출처의 문장은 §8에 「미열람」으로 모았다.
- **예산.** 세션 WebSearch 한도 200회를 에이전트 넷이 소진해, 후반 갈래(OpenAI 2026, Cochrane 2026)는 추가 탐색을 못 했다. §7에 적었다.
- **원칙.** 본문에는 원문 문자열로 확인한 것만 적었다. 날짜는 페이지에서 확인한 것만 단정하고, 에이전트 보고에만 있는 날짜는 「(보고)」로 표시했다.

## 1. 검증 결과 요약

| 갈래 | 보고서 항목 | 내가 대조한 페이지 | 원문과 다른 것 | 단서 |
|---|---|---|---|---|
| A 유명인 | 42건(15명) | 24 grep + 3 WebFetch | 인용 문자열 오류 0 | 귀속 정정 3건(§8), 미열람 2곳(CACM·X) |
| B 기관 | 22건 | 19 grep + Europe PMC | 0 | Lancet 원문 미열람, 2차 출처 간 수치 불일치(§4.6) |
| C 실증 | 30여 건 | arXiv 초록 27 + 페이지 3 | 초록 수준 0 | 본문에만 있는 수치 3건 미대조(§8) |
| D 방법 | 29건 | 12 grep | 0 | 에이전트가 「인용 드리프트」로 보고한 건은 오경보(§8) |

네 보고서 모두 「열었다/스니펫만」을 구분해 적었고, 표본 대조에서 인용 문자열 오류는 나오지 않았다. 대신 조사 과정 자체에서 이 문서의 주제인 실패가 세 번 관측됐다. 검색 요약이 Gary Marcus 글에 없는 문장을 인용부호로 붙여 유통시킨 것(WebFetch로 부재 확인), 에이전트가 Weng의 요약문을 Weng 본인의 처방으로 귀속한 것, 에이전트가 같은 페이지의 두 문장(요약 절과 녹취 절)을 「드리프트」로 오판한 것이다.

## 2. 결론 다섯 줄

1. **생성이 싸지고 검증이 병목이라는 진단은 2026년에 합의에 가깝다.** Karpathy(4월), Tao(3·5·8월), DeepMind 정책팀(7월), NeurIPS 2026 워크숍(12월 예정)이 각자의 말로 같은 문장을 썼다. 다만 이들이 말하는 「검증 가능」의 본보기는 수학·코드다. Tao는 그 밖의 영역에서 AI의 실수가 「검증 불가능(unverifiable)」하다고 명시했다. 문헌 정리는 그 밖의 영역이다.
2. **존재 검사는 거의 풀렸고, 지지 검사는 안 풀렸다.** 인용이 실재하는지는 도구가 88–97%로 잡는다(§5.7). 실재하는 인용이 그 주장을 실제로 지지하는가는 최상위 모델도 39–77%였고(§5.2), 그 비율 자체가 검증기 엄격도에 따라 3%에서 18%까지 흔들린다(Goo 2026). 「논문이 있다」까지만 확인하는 검증은 거의 아무것도 재지 않는다.
3. **오류의 다수는 누락이고, 누락은 감사에 저항한다.** 추출 오류 중 누락·오기가 91.4%, 조작은 0.7–14.4%였다(Oami 2026). 최상위 모델도 평가 근거의 30%, 한계 서술의 25%만 회수했다(SciLitBench). 모델은 심어 둔 과잉 포함을 누락보다 6–7배 자주 잡는다(Chen 2026). 「빠진 게 있나 다시 봐라」는 가장 약한 검사다.
4. **다시 돌리기와 모델 여러 개는 독립 검증이 아니다.** 같은 설정의 GPT-5.4 두 번이 1,131건 중 94건에서 달랐고(Figalová 2026), 심판 9개가 유효 표 2개분의 정보만 냈다(Kohli 2026). AI 리뷰어끼리의 겹침은 21%, 사람끼리는 3%였다(Kim 2026). 두 번째 모델은 상관된 검사다.
5. **작동하는 것은 결정론적 도구, 사람의 표본 판독, 출처 스팬 강제다.** 아카이브 대조 도구는 미해결 URL을 6–79배 줄였고(Rao 2026), 사람은 라벨러보다 감사자로 쓸 때 60.8%→90.9%가 됐다(DeepFact). Husain은 「검증이 어렵다」는 말을 제품 결함으로 보고 출처 표시를 답으로 들었다.

## 3. 2026년 유명인의 발언

### 3.1 Terence Tao (UCLA)

- **ICM 2026 에세이 「Mathematics in the age of AI」**(arXiv 2608.16753, 2026-08-17). 발표 문턱을 이렇게 정한다. "if the authors cannot convincingly demonstrate that they are able to give a clear, expert-level talk on their results, one that is correct and properly attributed, then the result should not be published. A proof that no human can properly explain should be viewed as incomplete, even if it has been formally verified." 「저자가 자기 결과에 대해 정확하고 출처가 제대로 밝혀진, 명확한 전문가 수준의 발표를 할 수 있음을 설득력 있게 보여 주지 못하면 그 결과는 출판되지 않아야 한다. 어떤 사람도 제대로 설명할 수 없는 증명은 형식 검증을 통과했더라도 미완성으로 보아야 한다.」 형식 검증의 뜻과 새 실패 모드를 이렇게 적는다. "A formally verified proof is, after all, precisely a proof whose correctness no longer depends on the reputation or the diligence of its author. But now a new failure mode appears. What if an AI tool generates a lengthy proof that is verified to be correct, but which nobody — not even the humans who prompted the tool — understands?" 「형식 검증된 증명이란 결국 그 정확성이 더는 저자의 명성이나 성실함에 의존하지 않는 증명이다. 그런데 이제 새로운 실패 모드가 나타난다. AI 도구가 정확하다고 검증된 긴 증명을 만들어 냈는데, 그 도구에 프롬프트를 준 사람조차 아무도 이해하지 못한다면 어떻게 되는가?」 자동 필터의 한계도 명시한다. "passing an automatic filter is not a substitute for community acceptance; I do not believe that human referees can be removed from the publication process." 「자동 필터를 통과하는 것은 학계의 수용을 대신하지 못한다. 나는 출판 과정에서 사람 심사자를 빼낼 수 있다고 믿지 않는다.」 리뷰 부담을 줄이는 규칙으로는 다음을 싣는다. "Make it easier for your peers to review your work by disclosing tool use, giving precise and complete references to previous results, and providing formal proofs where feasible and appropriate." 「도구 사용을 공개하고, 선행 결과에 대한 정확하고 완전한 참고문헌을 제시하고, 가능하고 적절한 곳에는 형식 증명을 제공하여 동료가 당신의 연구를 검토하기 쉽게 만들라.」
  - 시나리오로 옮기면: 정리표를 받은 사람이 그 표로 전문가 수준의 발표를 할 수 있어야 검증이 끝난 것이다. 맞기만 하고 이해되지 않은 표는 미완성이다.
- **Palomar 등록소 공지**(블로그, 2026-08-18). "In recent months there has been a proliferation of AI-generated proofs of various old and new results, some of which have been formalized in the proof assistant language Lean. However, checking that a given Lean repository actually proves the claimed statement is somewhat non-trivial, especially for an audience which is not expert in the use of Lean: one has to first check that the claimed formal Lean statements have proofs that typecheck, that the proofs do not contain any "cheats" such as adding additional axioms, and that the formal statements also match (in a semantic sense) the informal description of the claimed results." 「최근 몇 달 사이 오래된 결과와 새 결과에 대한 AI 생성 증명이 급증했고, 그중 일부는 증명 보조기 언어 Lean으로 형식화되었다. 그러나 주어진 Lean 저장소가 실제로 주장된 명제를 증명하는지 확인하는 일은 다소 까다롭다. 특히 Lean 사용에 전문가가 아닌 독자에게는 그렇다. 먼저 주장된 형식 Lean 명제에 타입 검사를 통과하는 증명이 있는지, 증명에 공리를 추가하는 식의 「속임수」가 없는지, 그리고 형식 명제가 주장된 결과의 비형식 서술과 (의미상) 일치하는지 확인해야 한다.」 검사 둘 중 "the second check (b) is non-deterministic, being performed by a large language model" 「두 번째 검사 (b)는 대형 언어 모델이 수행하므로 비결정적이다」이고, "the checks in (a) and (b) fall well short of what a proper human peer review of a submission for novelty, interest, and accuracy would give; in particular, Palomar is not a peer-reviewed journal." 「검사 (a)와 (b)는 투고물의 새로움·흥미·정확성에 대한 제대로 된 사람 동료 심사가 주는 것에 한참 못 미친다. 특히 Palomar는 동료 심사 학술지가 아니다.」
  - 시나리오로 옮기면: 검사를 세 겹으로 나눈다. (a) 인용 문자열이 PDF에 실재하는가(기계적), (b) 몰래 더한 전제가 없는가, (c) 요약문이 원문 조건과 의미상 일치하는가. Tao는 (c)를 LLM이 하는 비결정적 검사라고 따로 표시했다. 조건 드리프트 검사가 바로 이 자리다.
- **Dwarkesh Patel 인터뷰**(2026-03-20). "We're now in a situation where suddenly people can generate thousands of theories for a given scientific problem. Now we have to verify them, evaluate them." 「이제 우리는 한 과학 문제에 대해 갑자기 수천 개의 이론을 만들어 낼 수 있는 상황에 있다. 이제 그것들을 검증하고 평가해야 한다.」 "it has to be matched by an equal amount of verification, otherwise it's slop." 「그만큼의 검증이 짝을 이루어야 한다. 그렇지 않으면 쓰레기다.」 그리고 검증기가 공략당한다는 경고. "It's really important with these formal proof assistants that there are no backdoors or exploits you can use to somehow get your certified proof without actually proving it, because reinforcement learning is just so good at finding these backdoors." 「이런 형식 증명 보조기에는 실제로 증명하지 않고도 인증된 증명을 얻어 낼 뒷문이나 취약점이 없어야 한다는 점이 정말 중요하다. 강화학습은 그런 뒷문을 찾아내는 데 너무나 능하기 때문이다.」
  - 시나리오로 옮기면: 채점 루브릭을 모델이 볼 수 있으면 루브릭만 맞추는 답이 나온다. 검사 일부는 모델 밖에 둔다.
- **Nature 인터뷰**(2026-05, Tao 본인의 요약 페이지 teorth.github.io/tao-web/ai-views.html에서 확인, Nature 원문 미열람). "In almost any other application, the biggest Achilles heel of AI is that it makes unverifiable mistakes," ... "But in mathematics, almost uniquely, you can automatically check the output" 「거의 모든 다른 응용에서 AI의 가장 큰 아킬레스건은 검증할 수 없는 실수를 한다는 것이다. 그러나 수학에서는 거의 유일하게 출력을 자동으로 검사할 수 있다.」 같은 페이지의 규칙 문장(2025-11 블로그 댓글이라고 보고, 날짜 미확인). "I would caution against using AI tools without the ability to independently verify their output. Relying on these tools to compensate for their own mistakes is quite risky and can amplify the weaknesses of such tools, such as hallucination, sycophancy, or lack of grounding." 「출력을 독립적으로 검증할 능력 없이 AI 도구를 쓰는 것은 경계하라고 권한다. 이 도구들이 자기 실수를 스스로 보정하리라 믿는 것은 꽤 위험하며, 환각·아첨·근거 부재 같은 도구의 약점을 증폭할 수 있다.」
- **Mastodon**(2026-05-10). "out of three major components of the mathematical problem solving process - proof generation, proof verification, and proof digestion - the first two are being automated far more successfully than the third, leading to a new experience of "proof indigestion" in which proofs are being generated and even verified without being digested." 「수학 문제 풀이 과정의 세 주요 구성 요소, 즉 증명 생성·증명 검증·증명 소화 중에서 앞의 둘이 셋째보다 훨씬 성공적으로 자동화되고 있어, 증명이 생성되고 심지어 검증까지 되었는데 소화되지는 않는 「증명 소화불량」이라는 새로운 경험이 생기고 있다.」 이어서 "blindly optimizing various metrics for "digestibility", such as rubrics for mathematical exposition, can make the final product *worse* when viewed holistically." 「수학 서술 루브릭 같은 「소화 용이성」 지표를 맹목적으로 최적화하면 전체적으로 보았을 때 최종 산출물이 오히려 더 나빠질 수 있다.」
- **IEEE Spectrum**(2026, 날짜는 보고 2026-06-25). "If it wasn't for this formal verification layer, opening projects up without any safeguards would just be a disaster," ... "But in math, we can completely check and verify outputs, and this really filters out a lot of the rubbish." 「이 형식 검증 층이 없었다면 아무 안전장치 없이 프로젝트를 개방하는 것은 그냥 재앙이었을 것이다. 그러나 수학에서는 출력을 완전히 검사하고 검증할 수 있고, 이것이 쓰레기를 상당히 걸러 낸다.」

### 3.2 Andrej Karpathy

- **Sequoia Ascent 2026 요약·녹취**(본인 블로그, 2026-04-30). 요약 절: "My core automation framework is: Traditional software automates what you can specify. LLMs and reinforcement learning automate what you can verify." 「내 자동화 틀의 핵심은 이것이다. 전통 소프트웨어는 명세할 수 있는 것을 자동화한다. LLM과 강화학습은 검증할 수 있는 것을 자동화한다.」 녹취 절: "Traditional computers automate what you can specify in code. This latest round of LLMs can automate what you can verify. When frontier labs train these LLMs, they train them in giant reinforcement learning environments with verification rewards." 「전통적인 컴퓨터는 코드로 명세할 수 있는 것을 자동화한다. 이번 세대의 LLM은 검증할 수 있는 것을 자동화할 수 있다. 프론티어 연구소가 이 LLM들을 훈련할 때는 검증 보상이 있는 거대한 강화학습 환경에서 훈련한다.」 사람의 자리: "The agentic engineer does not blindly accept generated code. They design specs, supervise plans, inspect diffs, write tests, create evaluation loops, manage permissions, isolate worktrees, and preserve quality." 「에이전틱 엔지니어는 생성된 코드를 맹목적으로 받아들이지 않는다. 명세를 설계하고, 계획을 감독하고, diff를 검사하고, 테스트를 쓰고, 평가 루프를 만들고, 권한을 관리하고, 워크트리를 격리하고, 품질을 지킨다.」 "To the extent models remain jagged, it means you need to be in the loop. You need to treat them as tools and stay in touch with what they are doing." 「모델이 들쭉날쭉한 한, 당신이 루프 안에 있어야 한다는 뜻이다. 모델을 도구로 다루고 그것이 무엇을 하는지 계속 파악하고 있어야 한다.」 "Right now the agents are like interns. You still have to be in charge of aesthetics, judgment, taste, and oversight." 「지금 에이전트는 인턴 같다. 미적 감각·판단·취향·감독은 여전히 당신이 맡아야 한다.」 글쓰기 같은 연성 산출물에 대해서는 이렇게 말했다. "Ultimately, almost everything can be made verifiable to some extent, some things more easily than others. Even for writing, you can imagine having a council of LLM judges and getting something reasonable." 「결국 거의 모든 것은 어느 정도 검증 가능하게 만들 수 있다. 어떤 것은 더 쉽고 어떤 것은 더 어렵다. 글쓰기조차 LLM 심판 협의회를 두어 그럭저럭 괜찮은 결과를 얻는 것을 상상할 수 있다.」 이 「심판 협의회」는 §5.6의 Kohli 2026이 정량으로 반박한다.
- **autoresearch 저장소 README**(2026-03). 검증 원리가 문장이 아니라 구조에 있다. "It modifies the code, trains for 5 minutes, checks if the result improved, keeps or discards, and repeats." 「코드를 수정하고, 5분 훈련하고, 결과가 나아졌는지 확인하고, 유지하거나 버리고, 반복한다.」 "training runs for a fixed 5-minute time budget" 「훈련은 고정된 5분 시간 예산으로 돈다」 "The metric is val_bpb" 「지표는 val_bpb다」 "One GPU, one file, one metric." 「GPU 하나, 파일 하나, 지표 하나.」 채점 쪽 파일은 "Not modified" 「수정하지 않음」, 목표를 적는 `program.md`는 "This file is edited and iterated on by the human" 「이 파일은 사람이 편집하고 반복 개선한다」.
  - 시나리오로 옮기면: 값싸고 고정 비용인 검사 하나를 에이전트가 고칠 수 없는 자리에 두고, 「좋은 정리표」의 정의는 사람이 쓴다.

### 3.3 Simon Willison

- **「Don't be a meat proxy」**(2026-08-03). Willison: "Niklas Gruhn coins an excellent new term - meat proxy - for people who blindly copy and paste the output of AI systems to their peers." 「Niklas Gruhn이 AI 시스템의 출력을 동료에게 맹목적으로 복사해 붙이는 사람을 가리키는 훌륭한 새 용어 「고기 프록시(meat proxy)」를 만들었다.」 그가 인용·지지한 Gruhn의 문장: "By all means, prompt AI. But don't just relay the output. Read it, understand it, validate it, and then write a response in your own words (a decent certificate that you've done the prior steps)." 「얼마든지 AI에 프롬프트를 주라. 그러나 출력을 그냥 전달하지는 말라. 읽고, 이해하고, 검증한 다음, 자기 말로 답을 쓰라. 앞 단계를 실제로 했다는 꽤 괜찮은 증명서다.」 기억할 문장은 Gruhn의 것이고 Willison의 기여는 명명과 확산이다.
- **「More than just code review」**(2026-08-22). "The key skill required to make productive use of coding agents is being able to confidently instruct them on how to make changes and then confidently verify that those changes have been applied in the correct way. Sometimes this involves reviewing every line of code they have written, but there are other ways to achieve that goal. Eyeballing every line of code has never been the most effective way to validate a change to a piece of software." 「코딩 에이전트를 생산적으로 쓰는 데 필요한 핵심 기술은, 어떻게 바꿀지를 자신 있게 지시하고 그 변경이 올바르게 적용되었는지를 자신 있게 검증할 수 있는 능력이다. 때로는 에이전트가 쓴 모든 줄을 검토해야 하지만, 그 목표를 이루는 다른 방법도 있다. 코드를 한 줄씩 눈으로 훑는 것이 소프트웨어 변경을 검증하는 가장 효과적인 방법이었던 적은 없다.」
  - 시나리오로 옮기면: 40편을 다시 다 읽는 것이 최선의 검사가 아니다. 인용 문자열 존재, DOI 해결, 조건 일치 같은 표적 검사가 전수 재독을 이길 수 있다.
- 2026-09-08 Navier–Stokes 글은 검증 방법을 말하지 않는다(에이전트 A·D 모두 동일 판정).

### 3.4 Kevin Buzzard, Timothy Gowers (수학자)

- **Buzzard, 「FLT: Anthropic has beaten me to it」**(Xena Project, 2026-09-04). 실제 검증 절차의 가장 좋은 예다. 1층은 기계적 전수 검사: "I've compiled the code base and run comparator on it — it checks out." 「코드베이스를 컴파일하고 comparator를 돌렸다. 통과했다.」 2층은 사람의 표적 정독: "Because I asked an agent to look over the repository and report on everything which was not a mathematical definition or proof of a theorem, and then extremely carefully inspected the 100 or so lines of code which did not fit into this category with Claude and concluded that it was just defining a new convenience tactic." 「에이전트에게 저장소를 훑어 수학적 정의나 정리의 증명이 아닌 모든 것을 보고하게 했고, 그 범주에 들지 않는 100줄 남짓의 코드를 Claude와 함께 극도로 신중하게 검사한 결과 그것이 단지 새 편의 tactic을 정의하는 것뿐임을 확인했기 때문이다.」 그리고 맞음과 가치를 분리한다. "Note that mathematically this work of anthropic tells us essentially nothing" 「수학적으로 Anthropic의 이 작업은 우리에게 본질적으로 아무것도 말해 주지 않는다는 점에 유의하라」 "the formalization just faithfully follows the early literature on the proof and adds nothing." 「이 형식화는 증명에 관한 초기 문헌을 충실히 따르기만 하고 아무것도 더하지 않는다.」
  - 시나리오로 옮기면: 기계가 보증할 수 있는 부분(인용 문자열 일치)은 전수로 돌리고, 기계가 보증 못 하는 잔여(연결 문장·종합)만 사람이 정독한다. 충실한 표가 곧 가치 있는 표는 아니다.
- **Gowers, 「What sort of maths are LLMs good at?」**(2026-08-12). 사람들의 전형적 반응을 이렇게 옮긴다. "People often seem to react by saying something like, "Initially I was amazed that the problem had been solved, but on closer inspection I realized that the approach was actually not all that novel, and one that with the right small hint a suitably expert human could have found quite easily."" 「사람들은 흔히 이렇게 반응하는 듯하다. 「처음엔 문제가 풀렸다는 데 놀랐지만, 자세히 보니 접근법이 사실 그렇게 새롭지 않았고, 적절한 작은 힌트만 있으면 충분히 전문가인 사람이 꽤 쉽게 찾았을 것이었다.」」 본인의 판단: "if an LLM has what looks like the kind of idea that could only be the result of 'deep thought' about a problem, we can never be sure that it has actually carried out that deep thought, as opposed to finding a model argument already in the literature" 「LLM이 어떤 문제에 대한 「깊은 사고」의 결과로만 나올 수 있어 보이는 아이디어를 내놓았을 때, 그것이 문헌에 이미 있는 본보기 논증을 찾아낸 것이 아니라 실제로 그 깊은 사고를 수행했는지 우리는 결코 확신할 수 없다」
  - 시나리오로 옮기면: 첫인상은 예측 가능한 방향으로 틀린다. 「40편을 다 읽은 게 분명하다, 이렇게 꼼꼼하니」는 추론이 아니다. 주장 단위 출처 대조만이 읽음과 지어냄을 구분한다.

### 3.5 Lilian Weng, Hamel Husain, Shreya Shankar, Eugene Yan, Sebastian Raschka

- **Weng, 「Harness Engineering for Self-Improvement」**(Lil'Log, 2026-07-04). 본인 문장: "A system can write a plausible manuscript while still having fabricated citations, implementation drift, or weak experimental results." 「시스템은 조작된 인용, 구현 드리프트, 약한 실험 결과를 안고서도 그럴듯한 원고를 쓸 수 있다.」 "Humans should move up the stack, not be removed from the loop, meaning that human should provide oversight at the right time, at the right abstraction level and our system design should consider when and how to set up such touch points." 「사람은 루프에서 제거될 것이 아니라 스택의 위로 올라가야 한다. 즉 사람은 적절한 때에 적절한 추상화 수준에서 감독을 제공해야 하고, 시스템 설계는 그런 접점을 언제 어떻게 둘지를 고려해야 한다.」 ScientistOne(Meng 2026, arXiv 2605.26340)을 소개하는 문장: "every claim (citation, numerical, methodological, conclusion) must trace to an evidence source and is audited by Chain-of-Evidence checks." 「모든 주장(인용·수치·방법·결론)은 근거 출처로 추적되어야 하고 Chain-of-Evidence 검사로 감사된다.」 네 가지 주장 유형은 Weng의 처방이 아니라 ScientistOne의 설계다(에이전트 A의 귀속을 정정).
- **Husain, 「'It's Hard to Eval' Is a Product Smell」**(2026-06-29). "Artifacts that are hard for you to verify are often hard for users too. In the worst case, users have to redo the work from scratch to verify the output." 「당신이 검증하기 어려운 산출물은 사용자에게도 어려운 경우가 많다. 최악의 경우 사용자는 출력을 검증하려고 작업을 처음부터 다시 해야 한다.」 "A common thread across these examples is provenance. The fastest way to make an output checkable is to show where each part came from, with links to see more detail." 「이 예들을 관통하는 공통점은 출처(provenance)다. 출력을 검사 가능하게 만드는 가장 빠른 길은 각 부분이 어디서 왔는지를 더 자세히 볼 링크와 함께 보여 주는 것이다.」
- **Husain & Saha, 「Do Automated Evals Work?」**(2026-09-02). 사람이 라벨한 오류를 자동 시스템이 다시 찾게 한 실험. "The best recovered 87 percent of failures flagged by humans. Additionally, every system found issues humans missed. But there were downsides. Fully automated approaches always failed to catch interactions that "looked correct" but fell short of providing a great user experience. The systems also flagged a fair number of issues that were not failures, which added some noise." 「최고 시스템은 사람이 표시한 실패의 87%를 되찾았다. 게다가 모든 시스템이 사람이 놓친 문제를 찾았다. 그러나 단점이 있었다. 완전 자동 접근은 「맞아 보이지만」 좋은 사용자 경험에는 못 미치는 상호작용을 항상 잡지 못했다. 또 실패가 아닌 것도 상당수 표시해 잡음을 더했다.」
  - 시나리오로 옮기면: LLM 심판은 다수를 잡되 「맞아 보이는」 부류를 체계적으로 놓친다. 조건이 떨어진 요약이 정확히 그 부류다.
- **Husain & Shankar, evals FAQ 「error analysis」**(2025-06-27 게재, 2026-09-01 수정). "Start by annotating at least 30 traces yourself before reviewing suggestions from an agent." 「에이전트의 제안을 검토하기 전에 최소 30개의 트레이스를 직접 주석 달면서 시작하라.」 "A working pool of roughly 100 diverse traces is a useful guardrail for this human-agent loop." 「대략 100개의 다양한 트레이스 풀이 이 사람-에이전트 루프의 유용한 가드레일이다.」 종료 기준은 "theoretical saturation, meaning new reviews stop revealing failure modes or changing existing ones." 「이론적 포화, 즉 새로 검토해도 새 실패 유형이 드러나지 않고 기존 유형도 바뀌지 않는 상태.」
- **Shankar, 「Exploring Agent-Assisted Qualitative Analysis」**(2026-05-21). 개별 코드 검증과 군집 검증의 비용 차이. "Validating axial codes consists of more steps: given two codes, do these codes belong together or should they belong in different clusters? And does the axial code name actually capture the cluster? This requires O(n²) comparisons, over pairs of codes, which is not feasible for humans. Moreover, without example tweets under each category and provenance from category back to evidence, I struggled to truly understand the definition of some of these clusters." 「축 코드(axial code) 검증은 단계가 더 많다. 두 코드가 주어지면 이들이 함께 묶여야 하는가, 아니면 다른 군집에 속해야 하는가? 그리고 축 코드의 이름이 실제로 그 군집을 포착하는가? 이것은 코드 쌍에 대해 O(n²)번의 비교를 요구하며, 사람에게는 불가능하다. 게다가 각 범주 아래 예시 트윗과 범주에서 근거로 되돌아가는 출처가 없으면, 나는 이 군집 중 일부의 정의를 제대로 이해하기 어려웠다.」 "Vague codes are easy to believe and impossible to act on." 「모호한 코드는 믿기는 쉽고 행동으로 옮기기는 불가능하다.」
  - 시나리오로 옮기면: 「찾아라」의 검증은 행마다 O(1)이고, 「정리하라」의 검증은 O(n²)다. 범주마다 소속 레코드와 근거 역참조를 강제해야 범주가 반증 가능해진다.
- **Yan, 「How to Work and Compound with AI」**(2026-05). "I think of verification as a ladder. The bottom is cheap and deterministic; the top is expensive and requires judgement. We want to address issues at the lowest possible rung." 「나는 검증을 사다리로 생각한다. 맨 아래는 싸고 결정론적이고, 맨 위는 비싸고 판단이 필요하다. 문제는 가능한 가장 낮은 칸에서 처리하려 한다.」 "Shift verification left; catch errors at write time." 「검증을 왼쪽으로 옮기라. 오류는 작성 시점에 잡으라.」 "For long-running tasks, have models watch models. Long sessions can drift as errors build up. One fix is to run a secondary session with fresh context to read the original spec and the recent turns..." 「오래 도는 작업에서는 모델이 모델을 지켜보게 하라. 긴 세션은 오류가 쌓이면서 표류할 수 있다. 한 해법은 새 컨텍스트의 보조 세션을 띄워 원래 명세와 최근 턴을 읽게 하는 것이다.」
- **Raschka, 「Controlling Reasoning Effort in LLMs」**(2026-07-18). RLVR 훈련의 사실: "The intermediate reasoning trace is ignored during RLVR; only the final answer and response format determine the reward." 「RLVR에서 중간 추론 흔적은 무시된다. 최종 답과 응답 형식만이 보상을 결정한다.」 "These <think> and </think> tags are cosmetic with respect to reasoning ability. They do not make the model reason" 「이 <think>와 </think> 태그는 추론 능력과 관련해서는 장식이다. 모델을 추론하게 만들지 않는다.」
  - 시나리오로 옮기면: 모델의 「왜 이 주장을 뽑았는가」 설명은 진실성으로 최적화된 적이 없다. 설명이 아니라 주장 대 원문을 검사한다.

### 3.6 Andrew Ng, Ethan Mollick

- **Ng, The Batch 「Three Key Loops for Building Great Software」**(2026-06-26). "Given a product specification and optionally a set of evals (that is, a dataset against which to measure performance), we can have an AI agent write code, test its work, and keep iterating until the code is bug-free and meets its specification." 「제품 명세와 선택적으로 평가 세트(즉 성능을 재는 데이터셋)가 주어지면, AI 에이전트가 코드를 쓰고 자기 작업을 테스트하고 코드에 버그가 없고 명세를 충족할 때까지 반복하게 할 수 있다.」 "I see humans as having a significant context advantage over current AI systems" 「나는 사람이 현재 AI 시스템에 비해 상당한 맥락 우위를 가진다고 본다」 "So long as the human knows something the AI does not, human-in-the-loop is needed to to inject that knowledge into the system." 「사람이 AI가 모르는 것을 알고 있는 한, 그 지식을 시스템에 주입하려면 사람이 루프 안에 있어야 한다.」
  - 시나리오로 옮기면: 40편 중 3편을 사람이 먼저 손으로 추출해 작은 정답 세트를 만들고, 나머지 37편에 투입하기 전에 그 세트로 재라.
- **Mollick, 「The Overhang」**(2026-09-18). "Making great things with AI means knowing which AI outputs to keep, which to discard, and which to use as raw material for something the AI would never have generated on its own." 「AI로 훌륭한 것을 만든다는 것은 어떤 AI 출력을 남기고, 어떤 것을 버리고, 어떤 것을 AI가 혼자서는 결코 만들지 못했을 무언가의 원재료로 쓸지를 아는 것이다.」 자기 사례: "I chose them, I knew enough about Zork and Eco and my own book to see where the AI went wrong, and to ask for a second version when the first wasn't right." 「내가 그것들을 골랐고, Zork와 Eco와 내 책에 대해 AI가 어디서 틀렸는지 알아볼 만큼 알고 있었고, 첫 버전이 맞지 않을 때 두 번째 버전을 요구할 수 있었다.」
  - 시나리오로 옮기면: 검증 능력은 검증자의 영역 지식에 묶인다. KV 캐시를 모르는 사람이 표를 검토하면 검토의 외양만 남는다.

### 3.7 집단 성명·기관 논고

- **NeurIPS 2026 워크숍 「Verification in the Age of AI Scientists」**(조직위: Marinka Zitnik(Harvard), Priya Donti(MIT), Emilien Dupont(Google DeepMind) 외, 2026-12 개최 예정, 페이지 2026-09 확인). "The bottleneck for AI for Science is no longer hypothesis generation, it is verification." 「과학을 위한 AI의 병목은 더는 가설 생성이 아니라 검증이다.」 "as AI Scientists scale beyond what humans can manually inspect, the central problem becomes which AI outputs deserve our scarce verification budget, and on what evidence we should be willing to act." 「AI 과학자가 사람이 수동으로 검사할 수 있는 범위를 넘어 확장될수록, 핵심 문제는 어떤 AI 출력이 우리의 희소한 검증 예산을 받을 자격이 있는가, 그리고 어떤 근거 위에서 행동해야 하는가가 된다.」
- **Google DeepMind 정책팀, 「Conjecture Machines」**(Wallace, Griffin, O'Neill, Luong, Larter, 2026-07). "AI agents are conjecture machines, making ideas and candidate solutions abundant and relatively cheap. Refutations remain physical and institutional — and so, costly and slow." 「AI 에이전트는 추측 기계다. 아이디어와 후보 해를 풍부하고 비교적 싸게 만든다. 반증은 여전히 물리적이고 제도적이며, 따라서 비싸고 느리다.」 Thang Luong의 말: "We are moving toward a future of serious 'proof indigestion' where AI generates breakthroughs faster than humans can review them" 「우리는 AI가 사람이 검토할 수 있는 속도보다 빠르게 돌파구를 생성하는 심각한 「증명 소화불량」의 미래로 가고 있다」 제안 중 하나: ""Human-AI Interaction Cards" — short records detailing the prompts and outputs that produced the key scientific insights." 「「인간-AI 상호작용 카드」, 즉 핵심 과학적 통찰을 낳은 프롬프트와 출력을 상세히 적은 짧은 기록.」
- **Leiden 선언**(Gary Marcus가 2026-06-07 글에서 인용). "Current automated techniques can produce plausible but unreliable (or even incorrect) arguments which are difficult to distinguish from correct mathematical proofs." 「현재의 자동화 기법은 올바른 수학적 증명과 구별하기 어려운, 그럴듯하지만 신뢰할 수 없는 (혹은 틀린) 논증을 만들어 낼 수 있다.」 그럴듯함과 맞음은 눈으로 구분되지 않으므로 검사가 필요하다는 수학자들의 공동 진술이다.

## 4. 2026년 기관·도구의 실천

### 4.1 Anthropic

- **Claude Science**(2026-06-30). 별도 리뷰어 에이전트: "As the pipeline runs, a reviewer agent inspects the outputs, flagging incorrect citations, untraceable numbers, and figures that don't match their underlying code, and self-correcting as it goes." 「파이프라인이 도는 동안 리뷰어 에이전트가 출력을 검사해, 잘못된 인용, 추적 불가한 수치, 바탕 코드와 맞지 않는 그림을 표시하고 진행 중에 스스로 고친다.」 출처 묶음: "When it generates a figure, Claude Science includes the exact code and environment that produced it, a plain-language description of how it was created, and the full message history." 「그림을 생성할 때 Claude Science는 그것을 만든 정확한 코드와 환경, 어떻게 만들어졌는지의 쉬운 말 설명, 그리고 전체 메시지 이력을 포함한다.」 문헌 리뷰 사례(Allen Institute의 Lecoq): "The sub-agents read through thousands of papers, pulling the central claim and the key quantitative finding, and storing them in an evidence state database." 「하위 에이전트들이 수천 편의 논문을 읽어 핵심 주장과 핵심 정량 결과를 뽑아 근거 상태 데이터베이스에 저장한다.」 "A key component of the workflow, enabled by Claude Science, is the use of actor-critic pairs: one agent creates content while a separate reviewer agent evaluates it for accuracy and citation fidelity." 「Claude Science가 가능하게 한 이 워크플로의 핵심 구성 요소는 행위자-비평자 쌍이다. 한 에이전트가 내용을 만들고, 별도의 리뷰어 에이전트가 정확성과 인용 충실도를 평가한다.」 리뷰어 에이전트의 검출률은 페이지에 없다. 같은 모델 계열이 검사한다는 점도 유의.
- **「Demystifying evals for AI agents」**(2026-01-09). 리서치 에이전트 평가의 채점기 조합: "Groundedness checks verify that claims are supported by retrieved sources, coverage checks define key facts a good answer must include, and source quality checks confirm the consulted sources are authoritative, rather than simply the first retrieved." 「근거성 검사는 주장이 검색된 출처로 뒷받침되는지 확인하고, 커버리지 검사는 좋은 답이 반드시 포함해야 할 핵심 사실을 정의하고, 출처 품질 검사는 참조한 출처가 단지 먼저 검색된 것이 아니라 권위 있는 것인지 확인한다.」 "LLM-as-judge graders should be closely calibrated with human experts to gain confidence that there is little divergence between the human grading and model grading. To avoid hallucinations, give the LLM a way out, like providing an instruction to return "Unknown" when it doesn't have enough information." 「LLM 심판 채점기는 사람 채점과 모델 채점 사이에 차이가 거의 없다는 확신을 얻기 위해 사람 전문가와 긴밀히 보정되어야 한다. 환각을 피하려면 LLM에 빠져나갈 길을 주라. 예컨대 정보가 충분하지 않을 때 「Unknown」을 반환하라는 지시다.」 마지막 조언: "Read the transcripts!" 「트랜스크립트를 읽어라!」
  - 시나리오로 옮기면: 「반드시 들어 있어야 할 사실 목록」을 에이전트 실행과 독립적으로 미리 쓰는 것이 재현율 검사의 가장 옮기기 쉬운 형태다.

### 4.2 Google DeepMind, OpenAI

- **Co-Scientist 블로그**(2026-05-19). "the majority of the system's computation is dedicated to verifying these hypotheses. By deeply cross-checking claims against scientific literature and data, the system ensures that claims remain grounded, factually accurate, and logically coherent." 「시스템 연산의 대부분은 이 가설들을 검증하는 데 쓰인다. 주장을 과학 문헌과 데이터에 대조하여 깊이 교차 검증함으로써, 시스템은 주장이 근거를 갖고 사실에 맞고 논리적으로 일관되게 유지되도록 한다.」 Reflection 에이전트는 "Acts as a "virtual peer reviewer," critically evaluating hypotheses for correctness, quality, and novelty." 「「가상 동료 심사자」로 행동하며 가설의 정확성·품질·새로움을 비판적으로 평가한다.」 검출률 수치는 없다.
- **Kalai, Nachum, Vempala, Zhang, 「Evaluating large language models for accuracy incentivizes hallucinations」**(Nature 653:1047–1051, 2026-04-22, PMC13216060에서 확인). "under standard scoring, guessing is a dominant strategy" 「표준 채점에서는 추측이 우세 전략이다」 "facts lacking repeated support in training data (such as one-off details) yield unavoidable errors" 「훈련 데이터에서 반복 뒷받침이 없는 사실(일회성 세부 사항 등)은 피할 수 없는 오류를 낳는다」 "Under open rubrics, accuracy is no longer at odds with humility" 「공개 루브릭에서는 정확도가 더는 겸손과 충돌하지 않는다」.
  - 시나리오로 옮기면: 「모든 주장을 찾아라」는 커버리지로 채점되는 요청이다. 이 논문이 말하는 「추측이 우세 전략」인 채점 체계다. 「모르면 비워라」에 점수를 주는 지시가 있어야 한다.

### 4.3 연구 도구: Elicit

- **Elicit, 「Evaluating Elicit's Systematic Literature Review Capabilities」**(2026-09-17). Cochrane 공개 리뷰 "994 unique reviews covering 38,493 study records" 「38,493개 연구 레코드를 포괄하는 고유 리뷰 994편」를 정답으로 삼아 단계별 재현율을 냈다. "Search: 95.0% recall on included studies, using only the review title as the query." 「검색: 리뷰 제목만을 질의로 써서 포함 연구의 95.0% 재현율.」 초록 선별 "96.9% sensitivity" 「민감도 96.9%」, 전문 선별 "Recall / sensitivity 99.5% Specificity 70.1% Precision 81.2% Accuracy 86.7%" 「재현율/민감도 99.5%, 특이도 70.1%, 정밀도 81.2%, 정확도 86.7%」, 기준별 1,133쌍 94.8%, 추출 "95.6% correct on Methods, Participants, and Interventions" 「방법·참여자·중재에서 95.6% 정답」. LLM 채점기의 사람 검사: "We randomly selected 25 of the answers that were graded correct to review by hand. We agreed with the grade for all but one of the answers (which was an ambiguous case). We also reviewed by hand all 17 answers that were graded wrong" 「정답으로 채점된 답 중 25개를 무작위로 골라 손으로 검토했다. 하나(모호한 경우)를 빼고 모두 채점에 동의했다. 오답으로 채점된 17개는 전부 손으로 검토했다」. 추출 평가는 공개 PDF를 받을 수 있었던 "198 studies across 98 reviews and 769 extraction answers" 「리뷰 98편의 연구 198건, 추출 답 769개」로 좁혀졌다. 업체 자체 보고다.
- **Elicit 제품 페이지**(2026-09-17 확인). "Elicit cites every AI-generated claim with the exact sentence or figure from the underlying paper." 「Elicit은 AI가 생성한 모든 주장에 바탕 논문의 정확한 문장이나 그림을 인용으로 붙인다.」 "Every decision is PRISMA-auditable with exclusion reasons, per-criterion scores, and supporting quotes." 「모든 결정은 제외 사유, 기준별 점수, 뒷받침 인용과 함께 PRISMA 감사가 가능하다.」 마케팅 수치("Up to 99.5% screening recall", "96% Data extraction accuracy")는 위 평가 글과 대조해 읽어야 한다.

### 4.4 학회

- **AAAI-26 AI 리뷰 파일럿**(arXiv 2604.13940, 2026-04-15). "generate reviews for all 22,977 full-review papers in less than a day." 「전체 심사 대상 논문 22,977편 모두의 리뷰를 하루 안에 생성.」 인용 검사: "We randomly sampled 100 reviews generated by the AAAI-26 AI review system and checked for hallucinated citations using the GPTZero API. There were 1356 citations in the sampled reviews. GPTZero identified 1346 of the citations as valid, and matched them to published work at the cited venues, with matching authors and titles. It labelled 8 citations as 'unsure,' and 2 citations as 'fake.'" 「AAAI-26 AI 리뷰 시스템이 생성한 리뷰 100건을 무작위 표집해 GPTZero API로 환각 인용을 검사했다. 표집된 리뷰에는 인용 1356건이 있었다. GPTZero는 그중 1346건을 유효하다고 판정하고, 인용된 학회의 출판물과 저자·제목이 일치함을 확인했다. 8건은 「불확실」, 2건은 「가짜」로 표시했다.」 표본은 22,977건 중 100건(0.4%)이다. 품질 검사는 "peer reviews of peer reviews" 「동료 심사에 대한 동료 심사」(Goldberg 2025) 방식을 따랐다.
- **NeurIPS 2026 Position Paper Track**(공식 블로그, 2026-06-02). 탐지기 점수로 "178 submissions (18.4% of all submissions) will be desk rejected" 「투고 178편(전체의 18.4%)이 데스크 리젝트된다」, "123 submissions (12.7%) will be requested to provide evidence of substantial human engagement" 「123편(12.7%)은 실질적 인간 관여의 증거 제출을 요구받는다」. 소명 방식은 과정 증명이다. "Authors must supply the Track Chairs with a link to an online version of their paper that has a version history including the work before and after the use of AI" 「저자는 트랙 의장에게 AI 사용 전후의 작업을 포함하는 버전 이력이 있는 논문 온라인판 링크를 제출해야 한다」.
  - 시나리오로 옮기면: 내용으로 검증이 안 될 때 과정(버전 이력, 중간 산출물)을 검증한다.

### 4.5 출판사·편집 기준

- **Springer Nature AI 지침**(날짜 없음, 2026-09-21 확인). "Researchers may use AIGC to gather and summarize literature or obtain conceptual clarifications but must verify the accuracy and authenticity of AI-generated information, especially because AI can produce fabricated or outdated references. Human oversight is mandatory to ensure scientific validity." 「연구자는 문헌을 모으고 요약하거나 개념을 명확히 하는 데 AIGC를 쓸 수 있지만, AI 생성 정보의 정확성과 진위를 반드시 검증해야 한다. 특히 AI는 조작되거나 오래된 참고문헌을 만들어 낼 수 있기 때문이다. 과학적 타당성을 보장하려면 사람의 감독이 필수다.」 "Use of AIGC must be fully and transparently declared, including tool versions, usage dates, prompts, and the extent of AI contribution within manuscripts." 「AIGC 사용은 도구 버전, 사용 날짜, 프롬프트, 원고 내 AI 기여 범위를 포함해 완전하고 투명하게 신고되어야 한다.」 리뷰어: "while AI may support reviewers, it cannot replace reviewer expertise, critique or judgement." 「AI가 심사자를 도울 수는 있어도 심사자의 전문성·비평·판단을 대신할 수는 없다.」
- **ICMJE 권고**(2026-01 갱신이라고 보고, 페이지에 판 날짜 없음). "Authors should carefully review and edit the result because AI can generate authoritative-sounding output that can be incorrect, incomplete, or biased." 「AI는 권위 있게 들리지만 틀리거나 불완전하거나 편향된 출력을 만들 수 있으므로, 저자는 결과를 신중히 검토하고 편집해야 한다.」 "Humans must ensure there is appropriate attribution of all quoted material, including full citations." 「사람은 인용된 모든 자료에 완전한 출처 표기를 포함한 적절한 귀속이 있는지 확인해야 한다.」 "Chatbots (such as ChatGPT) should not be listed as authors because they cannot be responsible for the accuracy, integrity, and originality of the work" 「챗봇(ChatGPT 등)은 연구의 정확성·완전성·독창성에 책임질 수 없으므로 저자로 올려서는 안 된다」.

### 4.6 The Lancet 조작 인용 감사

- **서지(Europe PMC로 확인).** Topaz M, Roguin N, Gupta P, Zhang Z, Peltonen LM. "Fabricated citations: an audit across 2·5 million biomedical papers." Lancet 407(10541):1779–1781, 2026-05-01, doi 10.1016/S0140-6736(26)00603-3. 동반 사설 Bauchner H, Rivara FP. "Fabricated references: a new threat to editorial integrity." 같은 호 1765–1766. 원문은 403으로 열지 못했다.
- **비율(내가 연 2차 출처 둘에서 일치).** Retraction Watch(2026-05-07): "about one in 277 papers published in the first seven weeks of 2026 referenced a paper that didn't exist. That was a jump from 2025's rate of one in 458 and 2023's one in 2,828." 「2026년 첫 7주에 출판된 논문 약 277편 중 1편이 존재하지 않는 논문을 인용했다. 2025년의 458편 중 1편, 2023년의 2,828편 중 1편에서 급증한 것이다.」 STAT(2026-05-07): "In 2023, 1 in 2,828 papers contained one or more fabricated references, but in 2025 that number had reached 1 in 458 — a sixfold increase in frequency. During the first seven weeks of 2026, the rate reached 1 in 277 papers." 「2023년에는 2,828편 중 1편이 하나 이상의 조작 참고문헌을 담았지만, 2025년에는 458편 중 1편에 이르러 빈도가 여섯 배가 되었다. 2026년 첫 7주 동안 비율은 277편 중 1편에 도달했다.」
- **건수(2차 출처 간 불일치, 합치지 않음).** Retraction Watch: "verify 97.1 million references, from which they identified 4,406 "fabricated" references that appeared in a total of 2,810 papers." 「참고문헌 9,710만 건을 검증하고, 그중 논문 2,810편에 등장한 「조작」 참고문헌 4,406건을 찾아냈다.」 STAT: "over 2 million papers and 97 million citations" 「논문 200만 편 이상과 인용 9,700만 건」 "around 4,000 fabricated citations among 2,800 papers" 「논문 2,800편에서 약 4,000건의 조작 인용」. The Scientist(WebFetch): "4,046 fabricated references ... across 2,810 papers" 「논문 2,810편에서 조작 참고문헌 4,046건」, "125.6 million references" 「참고문헌 1억 2,560만 건」. 4,046과 4,406은 자리바꿈 오기일 가능성이 있고, 97.1M과 125.6M은 검증 가능 참고문헌과 전체 참고문헌의 차이일 수 있으나 원문 없이 확정하지 않는다.
- **출판사 실천(STAT).** "The Science family of journals uses an automated tool to check references" 「Science 계열 학술지는 참고문헌을 검사하는 자동 도구를 쓴다」. JAMA·NEJM도 인용 검증 도구를 쓴다고 답했다. "more than a third of fabricated citations come from two publishers." 「조작 인용의 3분의 1 이상이 두 출판사에서 나온다.」

## 5. 2026년 실증 연구: 오류는 어디서 나는가

수치는 arXiv 초록에서 문자열로 확인한 것이다. 본문에만 있는 수치는 §8에 따로 적었다.

### 5.1 조작 인용(존재하지 않는 출처)

- **Zhao, Wang, Stuart, De Vaan, Ginsparg, Yin**(arXiv 2605.07723, 2026-05-08). "audit 111 million references across 2.5 million papers in arXiv, bioRxiv, SSRN, and PubMed Central" 「arXiv, bioRxiv, SSRN, PubMed Central의 논문 250만 편에 걸친 참고문헌 1억 1,100만 건을 감사」 "a conservative estimate of 146,932 hallucinated citations in 2025 alone" 「2025년 한 해에만 환각 인용이 보수적으로 146,932건」. Lancet 감사(PMC OA 부분집합, ~97–126M 참고문헌)와 다른 연구다. 두 연구를 섞어 「Lancet가 1억 1,100만 건」이라고 쓰면 오류다.
- **Ansari, 「Compound Deception」**(arXiv 2602.05930, 2026-02-05). NeurIPS 2025 조작 인용 100건 분류. "Total Fabrication (66%), Partial Attribute Corruption (27%), Identifier Hijacking (4%), Placeholder Hallucination (2%), and Semantic Hallucination (1%)" 「완전 조작(66%), 부분 속성 손상(27%), 식별자 가로채기(4%), 자리표시 환각(2%), 의미 환각(1%)」 "every hallucination (100%) exhibited compound failure modes" 「모든 환각(100%)이 복합 실패 모드를 보였다」 "appearing in 53 published papers (approx. 1% of all accepted papers)" 「출판 논문 53편(채택 논문의 약 1%)에 등장」 "Despite review by 3-5 expert researchers per paper" 「논문당 전문 연구자 3–5명의 심사에도 불구하고」. GPTZero 원 조사(2026-01-21)는 "4841 papers" 「논문 4841편」 "100 confirmed hallucinations ... spanning over 51 NeurIPS papers" 「NeurIPS 논문 51편에 걸친 확정 환각 100건」이라 53과 51이 어긋난다.
- **Russinovich, Siva Kumar, Salem, 「Phantom References」**(arXiv 2607.00738, 2026-07-01). 보수적 정의("identity-level failures: non-existent works and substantial author-list mismatches" 「정체성 수준의 실패, 즉 존재하지 않는 저작과 저자 목록의 상당한 불일치」)로 "While reference-level rates are usually below 1%, proceedings are large enough that paper-level failures are visible: in 2025, roughly one in twenty NeurIPS and USENIX Security papers contains at least two likely hallucinated academic-paper-like references" 「참고문헌 수준 비율은 보통 1% 미만이지만 학회록이 충분히 커서 논문 수준의 실패가 드러난다. 2025년 NeurIPS와 USENIX Security 논문의 약 20편 중 1편이 환각으로 추정되는 학술 논문형 참고문헌을 둘 이상 담고 있다」.
- **Bienz, Pearson, Garcia de Gonzalo, 「The Case of the Mysterious Citations」**(arXiv 2602.05867, 2026-02-05). HPC 학회 넷. "While none of the 2021 papers contained mysterious citations, every 2025 proceeding did, impacting 2-6% of published papers." 「2021년 논문에는 정체불명 인용이 하나도 없었지만 2025년 학회록은 모두 있었고, 출판 논문의 2–6%에 영향을 주었다.」 시스템 분야 표본이라 이 프로젝트와 가장 가깝다.
- **Xu 외, 「GhostCite」**(arXiv 2602.06718, 2026-02-06). 모델 13개의 인용 생성에서 "all models hallucinate citations at rate from 14.23% to 94.93%" 「모든 모델이 14.23%에서 94.93%의 비율로 인용을 환각한다」. AI/ML·보안 학회 논문 "2.2 million citations from 56,381 papers" 「논문 56,381편의 인용 220만 건」에서 "1.07% of papers contain invalid citations, with an 80.9% increase in 2025" 「논문의 1.07%가 무효 인용을 담고 있고 2025년에 80.9% 증가」. 설문에서 "76.7% of reviewers do not thoroughly check references" 「심사자의 76.7%는 참고문헌을 철저히 확인하지 않는다」.
- **Rao, Wong, Callison-Burch**(arXiv 2604.03173, 2026-04-03). 딥리서치 에이전트의 URL 인용. "3--13% of citation URLs are hallucinated -- they have no record in the Wayback Machine and likely never existed -- while 5--18% are non-resolving overall." 「인용 URL의 3–13%는 환각이다. Wayback Machine에 기록이 없어 아예 존재한 적이 없을 가능성이 크다. 전체적으로 5–18%는 해결되지 않는다.」 "Deep research agents generate substantially more citations per query than search-augmented LLMs but hallucinate URLs at higher rates." 「딥리서치 에이전트는 검색 증강 LLM보다 질의당 훨씬 많은 인용을 생성하지만 URL을 더 높은 비율로 환각한다.」 도구를 주면 "reduce non-resolving citation URLs by 6--79× to under 1%" 「해결되지 않는 인용 URL을 6–79배 줄여 1% 미만으로」.
- **Rao, Callison-Burch, 「BibTeX Citation Errors」**(arXiv 2604.03159, 2026-04-03). 검색 가능한 최상위 모델 셋이 "Overall accuracy is 83.6%, but only 50.9% of entries are fully correct; accuracy drops 27.7 pp from popular to recent papers" 「전체 정확도는 83.6%지만 항목 전체가 맞는 것은 50.9%뿐이다. 인기 논문에서 최근 논문으로 가면 정확도가 27.7포인트 떨어진다」. 결정론적 검색 도구 clibib 2단계로 "91.5% (+8.0 pp) and fully correct entries to 78.3%, with a 0.8% regression rate" 「91.5%(+8.0포인트), 완전 정답 항목 78.3%, 회귀율 0.8%」.
- **Chen 외, 「Where Fake Citations Are Made」**(arXiv 2604.18880, 2026-04-20). "9 models and 108,000 generated references" 「모델 9개, 생성 참고문헌 108,000건」 "author names fail far more often than other fields across all models and settings." 「모든 모델과 설정에서 저자명이 다른 필드보다 훨씬 자주 틀린다.」
- **Gao 외, 의학 문헌 검색**(arXiv 2603.22344, 2026-03-21). 무료판 플랫폼 5개, "2,000 references" 「참고문헌 2,000건」 "40 randomly-selected original articles" 「무작위 선택 원저 논문 40편」. "LLM platforms completely failed to retrieve correct reference data 47.8% of the time." 「LLM 플랫폼은 47.8%의 경우 올바른 참고문헌 데이터를 전혀 가져오지 못했다.」

### 5.2 귀속·충실성(실재하는 인용이 주장을 지지하지 않음)

- **Onweller 외, 「Cited but Not Verified」**(arXiv 2605.06635, 2026-05-07). 이 시나리오에 가장 중요한 수치. "even the strongest frontier models maintain link validity above 94% and relevance above 80%, yet achieve only 39-77% factual accuracy" 「가장 강한 프론티어 모델조차 링크 유효성 94% 이상, 관련성 80% 이상을 유지하면서도 사실 정확도는 39–77%에 그친다」 "Fact Check accuracy drops by approximately 42% on average across two frontier models as tool calls scale from 2 to 150, demonstrating that more retrieval does not produce more accurate citations." 「도구 호출이 2회에서 150회로 늘면 프론티어 모델 둘의 사실 검사 정확도가 평균 약 42% 떨어진다. 검색을 더 한다고 인용이 더 정확해지지는 않음을 보여 준다.」 검색을 더 한다고 근거가 더 맞아지지 않는다.
- **Goo 외, 「Evaluating and Guarding Citation Faithfulness in Agentic Scientific Synthesis」**(arXiv 2607.20527, 2026-07-10). OpenScholar·PaperQA2류를 대상으로. "On identical agent outputs the measured unsupported-citation rate ranges from about 3% to about 18% depending only on the verifier's strictness, and although verifiers agree on which citations are supported, they disagree on which to flag (negative-specific agreement 0.27 to 0.30), so no single flag set is trustworthy and cross-paper comparison is invalid without a named verifier and protocol." 「동일한 에이전트 출력에서 측정된 미지지 인용률이 검증기의 엄격도에만 따라 약 3%에서 약 18%까지 달라진다. 검증기들은 어떤 인용이 지지되는지에는 동의하지만 어떤 것을 표시할지에는 불일치하므로(음성 특이 일치도 0.27–0.30), 어떤 단일 표시 집합도 신뢰할 수 없고, 검증기와 프로토콜을 명시하지 않은 논문 간 비교는 무효다.」 대안은 사람 정답에 고정한 평가와 split-conformal 보증("a guarantee on catch rate" 「검출률에 대한 보증」). 검증기 재현율은 "recall 0.94 on the supported class, held out" 「지지 클래스에 대한 재현율 0.94, 홀드아웃」.
  - 시나리오로 옮기면: 「미지지 인용률 x%」라는 숫자는 어느 검증기로 어느 프로토콜에서 잰 것인지 없이는 비교 불가다.
- **Williams, 「Faithful by Design」**(arXiv 2607.09932, 2026-07-10). 임상시험 요약 1,800건. "Unsupported Claims was identified as the dominant failure mode across all three models, with a mean annotation score of 1.55 out of three." 「세 모델 모두에서 미지지 주장이 지배적 실패 모드로 확인되었고, 평균 주석 점수는 3점 만점에 1.55였다.」
- **Miyai 외, 「Paper Reconstruction Evaluation」**(arXiv 2604.01128, 2026-04-01). 발표 품질과 환각은 직교한다. "ClaudeCode achieves higher presentation quality at the cost of more than 10 hallucinations per paper on average, whereas Codex produces fewer hallucinations but lower presentation quality." 「ClaudeCode는 논문당 평균 10건 이상의 환각을 대가로 더 높은 발표 품질을 얻고, Codex는 환각이 적지만 발표 품질이 낮다.」 잘 정리된 표가 정확한 표의 증거가 아니다.

### 5.3 누락(재현율)

- **Zabaleta, Lin, 「SciLitBench」**(arXiv 2609.05505, 2026-08-29). 공개 가중치 모델 22개. "performance declines from 0.97 accuracy for publication year to 0.37 Jaccard overlap for computational approach, while the strongest models recover only 30% of annotated evaluation evidence and 25% of limitations." 「성능은 출판 연도의 정확도 0.97에서 계산 접근법의 Jaccard 겹침 0.37로 떨어지고, 가장 강한 모델도 주석된 평가 근거의 30%, 한계 서술의 25%만 회수한다.」 「모든 주장을 찾을 수 있나」에 인용할 숫자다.
- **Oami, Okada, Maeda, Nakada**(Frontiers in Digital Health, doi 10.3389/fdgth.2026.1799623, 2026). 오류 유형을 missing / incorrect / fabricated / other로 나눴다. "missing or incorrect data accounted for the majority of errors [91.4% (95% CI, 88.4–94.5)] across all models." 「모든 모델에서 누락 또는 오기 데이터가 오류의 다수[91.4%(95% CI 88.4–94.5)]를 차지했다.」 배경·결과 추출에서 누락 빈도는 ChatGPT-4o 67.3%·83.4%, Claude 3 Sonnet 57.7%·73.3%, Gemini 1.5 Pro 39.5%·92.6%였고, 조작 빈도는 2.7%·4.5%, 0.7%·10.0%, 14.4%·3.9%였다. 무오류 비율은 배경 81.6%(ChatGPT-4o)–92.4%(Claude 3 Sonnet), 결과 27.8%(Gemini 1.5 Pro)–80.7%(Claude 3 Sonnet). "Prompt engineering strategies resulted in only modest changes in extraction accuracy across models." 「프롬프트 엔지니어링 전략은 모델 전반에서 추출 정확도를 소폭만 바꾸었다.」
- **Figalová, Huestegge, Böckler-Raettig**(arXiv 2608.26885, 2026-08-27, 사전등록). "No workflow recovered all verified eligible records." 「어떤 워크플로도 검증된 적격 레코드를 전부 회수하지 못했다.」 사람과 GPT-5.4는 "82.3-82.9% recall" 「재현율 82.3–82.9%」, Gemini 3.1은 "83.9%"를 내되 "retained 56.7% of records" 「레코드의 56.7%를 남겼다」. 그리고 "Two nominally identical GPT-5.4 file-batch runs agreed on 91.7% of records but differed on 94 records, including 29 verified eligible records retained by only one run." 「명목상 동일한 GPT-5.4 파일 배치 실행 둘이 레코드의 91.7%에서 일치했지만 94건에서 달랐고, 그중 29건은 한 실행에서만 남긴 검증된 적격 레코드였다.」
  - 시나리오로 옮기면: 한 번 돌린 결과는 두 번째 실행이 찾았을 것을 알 수 없다. 같은 프롬프트를 두 번 돌린 대칭차가 누락의 하한 추정치다.
- **Shafqat, Patterson, Liss, 「Knowledge Synthesis Review Framework」**(arXiv 2608.12741, 2026-08-13). "Claude Sonnet 4 achieved the highest screening accuracy (82.8%) and GPT-5 the highest recall (91.8%) at the expense of lower specificity. Extraction exceeded 90% agreement for titles and sources but degraded in author and reference fields. Performance declined most in interpretive analysis and cross-source synthesis, where expert judgment remained essential." 「Claude Sonnet 4가 가장 높은 선별 정확도(82.8%), GPT-5가 특이도를 희생한 가장 높은 재현율(91.8%)을 냈다. 추출은 제목과 출처에서 90% 이상 일치했지만 저자와 참고문헌 필드에서 떨어졌다. 해석적 분석과 교차 출처 종합에서 성능이 가장 많이 떨어졌고, 여기서는 전문가 판단이 여전히 필수였다.」 기계적 필드 ≫ 저자·참고문헌 필드 ≫ 해석 ≫ 교차 종합의 기울기다. 이 시나리오는 가장 나쁜 끝에 있다.
- **Lahlou, Gouttebroze, Oraee, Madera, 「Writing literature reviews with AI」**(arXiv 2603.20235, 2026-03-08, 질적 사례 연구). "in our case there was only 20% overlap between paper selections by humans and the LLM." 「우리 경우 사람과 LLM의 논문 선택 사이의 겹침은 20%뿐이었다.」 함정 첫째는 "The bias of ignorance (you do not know what you do not get) in the selection of relevant papers." 「관련 논문 선택에서의 무지의 편향(무엇을 못 받았는지 모른다).」 그리고 역설: "Most pitfalls can be addressed by prompting, but only if the user knows the domain well enough to detect them. There is a paradox: producing a good AI-assisted review requires expertise that comes from reading the literature, which is precisely what AI was meant to reduce." 「대부분의 함정은 프롬프트로 다룰 수 있지만, 사용자가 그것을 알아볼 만큼 영역을 잘 알 때만 그렇다. 역설이 있다. 좋은 AI 보조 리뷰를 만들려면 문헌을 읽어서 얻는 전문성이 필요한데, 그것이 바로 AI가 줄여 주려던 것이다.」
- **Chen 외, 「Judging Is Not Enumerating」**(arXiv 2608.01000, 2026-08-02). 재현율 축의 가장 날카로운 진술. "models judge whether a candidate belongs far better than they author the set itself" 「모델은 집합 자체를 저술하는 것보다 후보가 속하는지를 판정하는 것을 훨씬 잘한다」 "The dominant error is omission, which resists audit: an over-inclusion is a token a reviewer can challenge, a missing member an absence whose discovery is the authoring problem itself. Models detect planted over-inclusions 6-7x more often than planted omissions, and a production deployment of 43,227 items fails omission-first at 10:1." 「지배적 오류는 누락이며, 누락은 감사에 저항한다. 과잉 포함은 검토자가 이의를 제기할 수 있는 토큰이지만, 빠진 구성원은 그것을 발견하는 일 자체가 저술 문제인 부재다. 모델은 심어 둔 과잉 포함을 심어 둔 누락보다 6–7배 자주 검출하고, 43,227개 항목의 실제 배치에서는 누락 우선 실패가 10:1이다.」
  - 시나리오로 옮기면: 「모든 주장을 찾아라」는 집합 저술 과제다. 후보를 넓게 생성한 뒤 소속을 판정하게 하고, 「빠진 것 없나」를 모델에게 묻는 것은 하지 않는다.
- **Xiong 외, 「AutoResearchBench」**(arXiv 2604.25256, 2026-04-28). 문헌 「발견」 단계의 한계. "achieve only 9.39% accuracy on Deep Research and 9.31% IoU on Wide Research" 「Deep Research에서 정확도 9.39%, Wide Research에서 IoU 9.31%에 그친다」. 주어진 40편을 처리하는 게 아니라 40편을 찾는 단계에 해당한다.

### 5.4 조건·확신 왜곡

- **Belem, Wu, Yao, Steyvers, Singh, Smyth, 「From 'May' to 'Is'」**(arXiv 2606.07951, 2026-06-06). "certainty distortion affects up to 75% of LM outputs and is systematically asymmetric in rewriting tasks with most LMs being 1.5-2x more likely to increase the expressed certainty than to decrease it. These effects can compound over repeated paraphrasing: in the medical domain, claude-haiku-4.5 increases certainty in 20% of examples after a single iteration, increasing to 40% after five iterations. Prompt-based interventions reduce overall certainty distortion but do not eliminate it." 「확신 왜곡은 LM 출력의 최대 75%에 영향을 주고, 다시 쓰기 과제에서 체계적으로 비대칭적이어서 대부분의 LM이 표현된 확신을 낮추기보다 높이는 경향이 1.5–2배다. 이 효과는 반복 패러프레이즈에서 누적될 수 있다. 의학 영역에서 claude-haiku-4.5는 한 번 반복 후 예시의 20%에서 확신을 높였고, 다섯 번 반복 후에는 40%로 늘었다. 프롬프트 기반 개입은 전체 확신 왜곡을 줄이지만 없애지는 못한다.」
  - 시나리오로 옮기면: 「읽고 → 추출하고 → 주제별로 재정리」의 단계마다 한정어가 떨어질 수 있고, 다시 쓸수록 누적된다. 이 프로젝트가 기록한 발췌→요약 조건 드리프트의 측정된 기전이다. Peters & Chin-Yee 2025(과일반화 26–73%)의 2026년 후속은 이 틀(확신 왜곡)로 나왔고, 직접 재현 연구는 찾지 못했다.

### 5.5 수치·구조 오류

- **Tan, D'Souza, 「Diagnosing Structural Failures in LLM-Based Evidence Extraction for Meta-Analysis」**(arXiv 2602.10881, 2026-02-11, IRCDL 2026). "Full meta-analytic association tuples are extracted with near-zero reliability, and long-context inputs further exacerbate these failures." 「완전한 메타분석 연관 튜플은 거의 0에 가까운 신뢰도로 추출되고, 긴 컨텍스트 입력은 이 실패를 더 악화시킨다.」 원인은 "systematic structural breakdowns, including role reversals, cross-analysis binding drift, instance compression in dense result sections, and numeric misattribution" 「역할 역전, 분석 간 결합 드리프트, 밀집된 결과 절에서의 인스턴스 압축, 수치 오귀속을 포함한 체계적 구조 붕괴」.
  - 시나리오로 옮기면: 「KV 캐시 특성 주장」은 (주장, 조건/설정, 수치, 출처)의 튜플이다. 튜플의 결합이 풀리는 것이 여기서 이름 붙은 실패다. 수치와 조건이 떨어져 붙는 것을 기본 위험으로 둔다.
- **Yang 외, 「When LLMs Read Tables Carelessly」**(arXiv 2606.32029, 2026-06-30). 표 값을 "incorrectly citing or omitting" 「잘못 인용하거나 누락」하는 오류가 "all tested models (1.7B to 20B parameters)" 「시험한 모든 모델(1.7B–20B 파라미터)」에서 났고, 참조 검사 critic으로 "improves answer accuracy up to 12.0%" 「답 정확도를 최대 12.0% 향상」, 4B critic이 "F1 score of 78.2%" 「F1 78.2%」. 최상위 모델은 범위 밖이다.

### 5.6 심판·패널·재실행의 한계

- **Kohli, 「Nine Judges, Two Effective Votes」**(arXiv 2605.29800, 2026-05-28). "the 9 judges effectively provide only about 2 independent votes' worth of information. Roughly three-quarters of the panel's nominal independence is lost because the models make the same mistakes on the same items." 「심판 9개가 사실상 독립 표 약 2개분의 정보만 제공한다. 모델들이 같은 항목에서 같은 실수를 하기 때문에 패널의 명목 독립성 중 약 4분의 3이 사라진다.」 "the panel's actual accuracy falls 8-22 percentage points short of what independent voting would achieve, and the best single judge matches or outperforms the full panel across all conditions." 「패널의 실제 정확도는 독립 투표가 냈을 것보다 8–22포인트 낮고, 최고 단일 심판이 모든 조건에서 전체 패널과 같거나 더 낫다.」 "established methods close at most 11% of this gap, even with access to the correct answers." 「확립된 방법들은 정답에 접근할 수 있어도 이 격차의 최대 11%만 좁힌다.」 Karpathy의 「심판 협의회」에 대한 정량 반박이다.
- **Kim 외, 「On the limits and opportunities of AI reviewers」**(arXiv 2605.20668, 2026-05-20). "45 domain scientists in Physical, Biological, and Health Sciences spent 469 hours rating 2,960 individual criticisms ... of 82 Nature-family papers" 「물리·생물·보건과학 분야 과학자 45명이 469시간을 들여 Nature 계열 논문 82편에 대한 개별 비평 2,960건을 평가했다」. GPT-5.2 리뷰어가 "60.0% vs. 48.2%, p = 0.009" 「60.0% 대 48.2%, p = 0.009」로 최상위 사람 리뷰어를 넘고 "a distinct 26% of issues no human raises" 「어떤 사람도 제기하지 않은 별개의 문제 26%」를 냈지만, "AI reviewers overlap far more than humans do (21% vs. 3% for cross-reviewer pairs)" 「AI 리뷰어끼리는 사람보다 훨씬 많이 겹친다(리뷰어 쌍 간 21% 대 3%)」.
  - 시나리오로 옮기면: AI 비평이 사람보다 못하지 않다. 그러나 두 번째 모델은 두 번째 사람보다 훨씬 적은 독립 신호를 준다.
- **Norman, Rivera, Hughes, 「Reliability without Validity」**(arXiv 2606.19544, 2026-06-17). 심판 21개, "approximately 541,000 individual judgments" 「약 541,000건의 개별 판정」. "kappa deflation between exact match and Cohen's kappa is universal (33--41 pp on MT-Bench), judge rankings shift by up to 14 positions across benchmarks, high test--retest reliability (>0.95) coexists with severe position bias (>0.10)" 「정확 일치와 Cohen의 κ 사이의 κ 수축은 보편적이고(MT-Bench에서 33–41포인트), 심판 순위는 벤치마크에 따라 최대 14위까지 바뀌며, 높은 재검사 신뢰도(>0.95)가 심한 위치 편향(>0.10)과 공존한다」. 일치율 하나로 심판을 믿지 말라는 뜻이다. 범용 벤치마크 결과라 근거종합 특화는 아니다.
- **Peng 외, 「RuVerBench」**(arXiv 2606.29920, 2026-06-29). 딥리서치·코딩 "2,458 instances" 「인스턴스 2,458개」의 루브릭 판정. "even the most advanced models achieve strong performance but still exhibit substantial noise" 「가장 앞선 모델조차 강한 성능을 내면서도 상당한 잡음을 보인다」 "batched verification presents a trade-off between accuracy and efficiency, and majority voting yields effective but diminishing returns." 「묶음 검증은 정확도와 효율 사이의 맞바꿈이고, 다수결은 효과가 있지만 수익이 감소한다.」
- **Wang 외, 「The Verification Horizon」**(arXiv 2606.26300, 2026-06-24). "A classical intuition holds that verifying a solution is easier than producing one. For today's coding agents, this intuition is being inverted" 「해를 검증하는 것이 만드는 것보다 쉽다는 것이 고전적 직관이다. 오늘의 코딩 에이전트에서는 이 직관이 뒤집히고 있다」 "Every verifier we can build is only a proxy for human intent, never the intent itself." 「우리가 만들 수 있는 모든 검증기는 사람 의도의 대리물일 뿐 의도 자체는 결코 아니다.」 "verification must co-evolve with the generator." 「검증은 생성기와 함께 진화해야 한다.」
- **Nguyen, Hao, Elazar, Tan, 「Benchmarking Agentic Review Systems」**(arXiv 2606.19749, 2026-06-18). 오류 주입 벤치마크. "The strongest configuration (OpenAIReview + GPT-5.5) catches 71.6% of injected errors" 「가장 강한 구성(OpenAIReview + GPT-5.5)이 주입된 오류의 71.6%를 잡는다」 "The union of detections across six models reaches 83.3% recall" 「모델 여섯의 검출 합집합은 재현율 83.3%에 이른다」. 배치 후 "Votes on its comments skew positive at 1.44 to 1, and the most common complaints are about false positives and minor nitpicks." 「댓글에 대한 투표는 1.44 대 1로 긍정에 기울고, 가장 흔한 불만은 오탐과 사소한 지적이다.」
- **DeepFact, Audit-then-Score**(arXiv 2603.05912, 2026-03-06). "unassisted experts achieve only 60.8% accuracy on a hidden micro-gold set of verifiable claims" 「도움 없는 전문가는 검증 가능한 주장의 숨은 마이크로 골드 세트에서 정확도 60.8%에 그친다」 "Across four AtS rounds, expert micro-gold accuracy rises to 90.9%, indicating experts are substantially more reliable as auditors than as one-shot labelers." 「AtS 네 라운드를 거치면 전문가의 마이크로 골드 정확도가 90.9%로 오른다. 전문가는 일회성 라벨러보다 감사자로서 훨씬 믿을 만하다는 뜻이다.」
- **Cho, Sun, 「When Should an AI Workflow Release?」**(arXiv 2605.12947, 2026-05-13). 생성-평가-수정 루프의 정지 문제. "Each iteration can improve the candidate, but it also creates a release decision" 「각 반복은 후보를 개선할 수 있지만 동시에 출시 결정을 만든다」. 해법은 "a hard-negative reference pool of high-scoring failures" 「높은 점수를 받은 실패들의 어려운 음성 참조 풀」 대비 보정과 "an e-process" 「e-프로세스」로 "validity under optional stopping" 「임의 정지 하의 타당성」. 반복 검사가 확신을 조용히 부풀리지 않게 하는 장치다.
- **Vivekanantha 외, 이중 LLM 추출**(Knee Surg Sports Traumatol Arthrosc 34(8):3011–3029, 2026-04-21 온라인, PMC13418397). "Across all 384 fields, both LLMs produced fully correct outputs in 315 (82%) cases, while at least one model was fully correct in 365 (95.1%)." 「전체 384개 필드에서 두 LLM 모두 완전히 맞은 경우는 315건(82%), 적어도 한 모델이 완전히 맞은 경우는 365건(95.1%)이었다.」 "Most errors were due to omission of minor details in complex domains such as surgical details." 「대부분의 오류는 수술 세부 사항 같은 복잡한 영역에서 사소한 세부의 누락이었다.」 "caution by human verifiers must be taken to minimise automation bias" 「자동화 편향을 최소화하려면 사람 검증자가 주의해야 한다」.
  - 시나리오로 옮기면: 두 모델의 불일치는 사람 검토를 보낼 좋은 라우팅 신호다. 그러나 둘이 함께 떨어뜨린 조건은 일치로는 안 잡힌다.

### 5.7 검출기 성능(존재·메타데이터 검사)

| 도구 | 논문 | 잡는 것 | 초록에서 확인한 성능 |
|---|---|---|---|
| urlhealth | Rao 2604.03173 | URL 실재 대 링크 부패 | 미해결 URL "6--79× to under 1%" 「6–79배 줄여 1% 미만」 |
| clibib | Rao 2604.03159 | BibTeX 필드 | 83.6%→91.5%, 완전 정답 50.9%→78.3%, 회귀 0.8% |
| CiteTracer | 2605.08583 (2026-05-09) | 12코드 필드 수준 분류 | "97.1% accuracy on the synthetic benchmark" 「합성 벤치마크 정확도 97.1%」, F1 97.0/95.8/98.5; 실세계 조작 957건(ICLR 2026 등) |
| CiteCheck | 2605.27700 (2026-05-26) | Exact/Minor/Major | "88.7 macro-F1 and 88.9% accuracy" 「macro-F1 88.7, 정확도 88.9%」, 물리학 982건 벤치 |
| CiteAudit | 2602.23452 (2026-02-26) | 조작 참고문헌 | 벤치 실재 6,475 + 조작 2,967(HTML 본문). 성능 수치는 §8 |
| RefChecker | 2607.00738 | 정체성 수준 실패 | 위 5.1 참조 |
| 기존 도구 5종 평가 | Badalova & Mayr 2607.22693 (2026-07-17) | CheckIfExist, HalluCiteChecker, Hallucinator, HalRef, RefChecker | "limited by reference extraction errors, incomplete metadata, limited database coverage, and inconsistent verification results" 「참고문헌 추출 오류, 불완전한 메타데이터, 제한된 데이터베이스 범위, 일관되지 않은 검증 결과에 제약된다」 |

존재·메타데이터 검사는 88–97%다. 주장 지지 검사에는 이에 맞먹는 수치가 없고, Goo 2026은 그 수치가 검증기를 명시하지 않으면 정의조차 안 된다고 본다.

## 6. 40편 시나리오에 적용: 2026년 근거가 지지하는 절차

각 단계에 근거와 조건을 붙였다. 「검증기」의 수치는 그 논문의 도메인·모델·연도에 묶인 것이라 이 코퍼스에 그대로 옮겨지지 않는다.

1. **결과를 보기 전에 「반드시 들어 있어야 할 주장」 목록을 쓴다.** 40편 중 3편을 사람이 먼저 손으로 추출해 정답 세트로 삼고(Ng), 그중 몇 개를 심어 둔 탐침으로 쓴다(Chen 2608.01000). Anthropic의 coverage check가 이 형식이다.
2. **모든 행에 출처 스팬을 강제한다.** 인용 문장 원문 + 위치. Elicit·Claude Science가 제품으로 구현했고, Husain은 이것을 「검증 가능한 산출물 설계」라 부른다. Shankar는 범주에도 소속 레코드와 역참조를 요구한다.
3. **결정론적 존재·포함 검사를 전수로 돌린다.** 인용 문자열이 PDF에 실재하는가, DOI가 해결되는가. 값싸고, 에이전트가 고칠 수 없는 스크립트에 둔다(autoresearch의 구조, Yan의 사다리 맨 아래 칸, Buzzard의 1층). 이 프로젝트의 `$KVCPOOL/tools/quotes_verbatim_check.py`가 이 자리다.
4. **추출을 독립적으로 다시 한다.** 다른 모델 또는 두 번째 실행. 대칭차가 사람 작업 대기열이다(Vivekanantha, Figalová). 「한쪽이 뽑고 다른 쪽이 검토」로 바꾸지 않는다(기존 문서 §3-1, Buscemi 2006). 두 모델이 함께 떨어뜨린 조건은 일치로 안 잡히므로 5·6단계가 따로 있다.
5. **사람이 30행 이상을 원문과 직접 대조하고 실패 분류를 만든다.** ~100행 풀에서 새 실패 유형이 안 나올 때까지(Husain & Shankar). 이때 사람은 처음부터 라벨하는 사람이 아니라 이의를 판정하는 감사자로 쓴다(DeepFact 60.8%→90.9%).
6. **조건 드리프트는 재정리 단계마다 검사한다.** 다시 쓸수록 확신이 부푼다(Belem 20%→40%). 각 재정리 후 (요약문, 원문 스팬+조건) 쌍을 NLI로 전수 스윕하고, 「이 문장이 암묵 가정한 조건은?」을 레코드만 보이는 새 컨텍스트에서 답하게 한다(기존 문서 §3-5). Tao의 Palomar 검사 (c)가 이 자리이고, 그는 이것을 비결정적 검사로 표시했다.
7. **LLM 심판은 사람 라벨로 보정한 뒤, 항목 단위로, 단일 최고 심판으로 쓴다.** 패널 9개는 표 2개분이다(Kohli). 일치율 대신 κ와 위치 편향을 본다(Norman). 「Unknown」 탈출구를 준다(Anthropic).
8. **종합 수준의 논리 일관성은 새 컨텍스트의 두 번째 독자에게 맡긴다**(Yan). 다만 그 독자가 AI면 첫 독자와 상관돼 있음을 전제한다(Kim 21% 대 3%).
9. **과정을 남긴다.** 코드·환경·메시지 이력(Claude Science), 버전 이력(NeurIPS 2026), 도구·버전·프롬프트 공개(Springer Nature, ICMJE, Leiden 선언). 내용으로 검증이 안 되는 것은 과정으로 검증한다.
10. **마지막으로 검증자가 그 표로 발표할 수 있는지 묻는다**(Tao). 맞기만 하고 소화되지 않은 표는 미완성이다. 검증 능력은 검증자의 영역 지식에 묶인다(Mollick, Lahlou의 역설).

## 7. 못 찾은 것

- **2026년 OpenAI의 딥리서치 인용 정확도·채점기 가이드.** openai.com이 403이라 아무 1차 자료도 열지 못했다. Prover-Verifier·confessions(2025-12)의 2026 후속도 찾지 못했다.
- **Cochrane의 2026년 AI 지침.** 검색 요약에 「2026-03 새 지침」이 있었으나 1차 문서를 열지 못했다. 인용 가능한 것은 2025-11-11 공동 성명(ED000178)이다.
- **METR의 검증 시간 측정.** 2026년 METR 보고 둘(2월 녹취 분석, 5월 설문)은 시간 절감을 재고 검토 시간을 분해하지 않는다.
- **UK AISI의 2026 토론·확장 감독 결과.** 2026년 항목 일곱 중 해당 없음. 가장 가까운 것은 Cooney, Africa, Irving의 거짓 탐지 논문(2026-06-17)이다.
- **Peters & Chin-Yee 2025의 직접 재현.** 2026년 후속은 확신 왜곡(Belem) 틀로만 나왔다.
- **7층(정의 비교가능성)을 다룬 2026년 자료.** 기존 문서와 같은 결론이다. 없다.
- **Jason Wei, Sam Altman, Demis Hassabis, Ilya Sutskever의 2026년 검증 관련 발언.** 없거나 X에만 있어 열 수 없었다. Wei의 「verifier's law」는 2025-07-15다.

## 8. 대조한 것 / 고친 것 / 뺀 것 / 2차 인용

**대조한 것.** 에이전트 넷의 인용 구절 약 150개를 원문 페이지 60여 곳(HTML grep 55, WebFetch 4, Europe PMC 3)에서 문자열로 확인했다. 초록·페이지 수준에서 원문과 다른 문자열은 없었다.

**고친 것(귀속).**
- Weng의 "every claim (citation, numerical, methodological, conclusion) must trace to an evidence source"는 Weng의 처방이 아니라 Meng 2026 ScientistOne을 소개하는 문장이다.
- Gowers의 "Initially I was amazed ..."는 Gowers 본인의 판단이 아니라 "People often seem to react by saying something like"로 소개한 전형적 반응이다.
- Marcus 2026-06-07의 "plausible but unreliable ..."는 Marcus의 말이 아니라 그가 인용한 Leiden 선언이다.
- 에이전트 D가 Karpathy 페이지에서 「인용 드리프트」로 보고한 두 문장(요약 절의 "Traditional software automates what you can specify"와 녹취 절의 "Traditional computers automate what you can specify in code")은 둘 다 페이지에 실재한다. 드리프트가 아니라 같은 글의 두 절이다.
- Oami 2026의 「누락 67–93%, 조작 0.7–14%」는 에이전트의 범위 요약이다. 본문의 모델별 수치(누락 39.5–92.6%, 조작 0.7–14.4%)로 바꿔 적었다.
- 「Lancet가 1억 1,100만 참고문헌을 감사」는 두 연구의 혼동이다. 1억 1,100만은 Zhao 외 arXiv 2605.07723이다.

**뺀 것(인용 금지, 원문 미확인).**
- Kambhampati의 "There will always be a role for some type of verifier. LLMs can't do it alone." 「어떤 종류든 검증기의 역할은 항상 있을 것이다. LLM 혼자서는 할 수 없다.」(CACM 2026-06-29). 페이지가 403.
- Gary Marcus 2026-06-12 글에 귀속된 "the failure isn't the AI, it's the assumption that you no longer have to check it" 「실패는 AI가 아니라 더는 확인하지 않아도 된다는 가정이다」. WebFetch로 부재 확인. 검색 요약이 만든 문장이다.
- CiteAudit의 성능 수치(97.3%/93.8%/F1 0.968, GPTZero 55.7%). 초록과 HTML v1 본문에 없다.
- GPTZero의 EY 보고서 조사(2026-05-14) 「27건 중 16건 조작」. 페이지 텍스트에 그 수치가 없다(그래픽으로 추정). 확인한 문장은 "it's crazy to accept citations on faith — even those from a reputable source like Ernst & Young." 「인용을 믿음으로 받아들이는 것은 미친 짓이다. Ernst & Young 같은 명망 있는 출처의 것이라도.」와 "One of our team members manually verified Hallucination Check's results" 「우리 팀원 한 명이 Hallucination Check의 결과를 수동으로 검증했다」뿐이다.
- Phantom References의 "~$0.04/paper". 초록에 없다.
- Lancet 동반 사설의 "91%". 원문 403.
- J Biomed Inform 2026 체계적 고찰의 저자명. 기존 문서가 「Shankar 2026」이라 적었고 이번 에이전트 C는 어느 페이지에서도 저자명을 확인하지 못했다. 수치(누락 60–74%)는 기존 문서의 Europe PMC 확인에 따른다.
- SciZoom(2603.16131)·Bakhshi(2604.19768)·DRACO(2602.11685)의 수치. 이번에 내가 열지 않았다.
- Tao의 Nature 원문, IEEE Spectrum 게재일, ICMJE 갱신일, Karpathy 강연 촬영일. 페이지에서 확인 못 한 날짜는 「(보고)」로 남겼다.
- Bengio LawZero 페이지의 "Its predictions are transparent, auditable and verifiable." 「그 예측은 투명하고 감사 가능하며 검증 가능하다.」는 문자열은 확인했으나 페이지에 날짜가 없어 2026년 발언으로 세지 않았다.
- Dario Amodei 「We Must Pace the Frontier」(2026-09)는 AI 기업의 절차 준수 검증에 관한 글이라 범위 밖으로 뺐다.

**2차 인용.**
- Tao의 Nature 발언(2026-05)은 Tao 본인의 요약 페이지에서 읽었다. Nature 원문 미열람.
- Lancet 감사의 모든 수치는 Retraction Watch·STAT(내가 열음)·The Scientist(WebFetch)에서 왔다. 4,046 대 4,406, 97.1M 대 125.6M은 미해결.
- Leiden 선언 문장은 Marcus 글에서, ScientistOne 설계는 Weng 글에서 읽었다. 각 원문 미열람.
- Tao OpenAI Forum(2026-03-10)의 문장은 OpenAI의 간접 서술("Tao says AI can make this worse by producing arguments that look polished while hiding the weak step" 「Tao는 AI가 약한 단계를 숨긴 채 세련되어 보이는 논증을 만들어 상황을 더 나쁘게 할 수 있다고 말한다」)이라 직접 인용으로 쓰지 않았다.

## 9. 출처 (확인된 것만, 갈래, 확인 경로)

| 출처 | 갈래 | 확인 경로 |
|---|---|---|
| Tao, Mathematics in the age of AI, arXiv 2608.16753 | A·D | HTML 본문 grep |
| Tao, Palomar 공지, 2026-08-18 | A·D | 블로그 grep |
| Tao, Dwarkesh Patel 인터뷰, 2026-03-20 | A | WebFetch + grep |
| Tao, tao-web/ai-views.html(본인 요약, 2026-09-17 갱신) | A·D | grep |
| Tao, Mastodon 116551624228986501, 2026-05-10 | A | Mastodon API |
| Tao, IEEE Spectrum 「AI in Mathematics Is Forcing Big Questions」 | A | grep |
| Karpathy, Sequoia Ascent 2026 summary, 2026-04-30 | A·D | grep(요약·녹취 양쪽) |
| Karpathy, autoresearch README | A·D | raw README grep |
| Willison, Don't be a meat proxy, 2026-08-03 | A·D | grep |
| Willison, More than just code review, 2026-08-22 | A·D | grep |
| Buzzard, FLT: Anthropic has beaten me to it, 2026-09-04 | A | grep |
| Gowers, What sort of maths are LLMs good at?, 2026-08-12 | A | grep |
| Weng, Harness Engineering for Self-Improvement, 2026-07-04 | A | grep |
| Husain, 'It's Hard to Eval' Is a Product Smell, 2026-06-29 | A | grep |
| Husain & Saha, Do Automated Evals Work?, 2026-09-02 | A | grep |
| Husain & Shankar, evals FAQ error analysis, 2026-09-01 수정 | D | grep |
| Shankar, Agent-Assisted Qualitative Analysis, 2026-05-21 | A | grep |
| Yan, How to Work and Compound with AI, 2026-05 | D | grep |
| Raschka, Controlling Reasoning Effort in LLMs, 2026-07-18 | A | grep |
| Ng, Three Key Loops, The Batch, 2026-06-26 | A | grep |
| Mollick, The Overhang, 2026-09-18 | A | grep |
| Marcus, Slop, productivity ..., 2026-06-07(Leiden 선언 인용) | A | grep |
| NeurIPS 2026 workshop Verification in the Age of AI Scientists | A | grep |
| DeepMind, Conjecture Machines, 2026-07 | B | grep |
| DeepMind, Co-Scientist blog, 2026-05-19 | B | grep |
| Anthropic, Claude Science, 2026-06-30 | B·D | grep |
| Anthropic, Demystifying evals for AI agents, 2026-01-09 | D | grep |
| Kalai et al., Nature 653:1047–1051, 2026-04-22 | B | PMC13216060 grep + Europe PMC 서지 |
| Elicit, Evaluating Elicit's SLR Capabilities, 2026-09-17 | B | grep |
| Elicit, systematic-review 제품 페이지 | D | grep |
| Biswas et al., AAAI-26 AI Review Pilot, arXiv 2604.13940 | B | HTML 본문 grep |
| NeurIPS 2026 PPT 블로그, 2026-06-02 | B | grep |
| Springer Nature AI guidance(날짜 없음) | B | grep |
| ICMJE Recommendations, authors and contributors | B | grep |
| Topaz et al., Lancet 407(10541):1779–1781 | B·C | Europe PMC 서지만 |
| Bauchner & Rivara, Lancet 407(10541):1765–1766 | B | Europe PMC 서지만 |
| Retraction Watch 2026-05-07; STAT 2026-05-07; The Scientist | B·C | grep / WebFetch |
| Rao, Wong, Callison-Burch, arXiv 2604.03173 | B·C·D | 초록 grep |
| Rao & Callison-Burch, arXiv 2604.03159 | C | 초록 |
| Badalova & Mayr, arXiv 2607.22693 | B | 초록 |
| Zhao et al., arXiv 2605.07723 | C | 초록 |
| Ansari, arXiv 2602.05930 | C | 초록 |
| GPTZero, NeurIPS 2025 audit, 2026-01-21 | C | grep |
| Russinovich et al., arXiv 2607.00738 | C | 초록 |
| Bienz et al., arXiv 2602.05867 | C | 초록 |
| Xu et al., GhostCite, arXiv 2602.06718 | C | 초록 |
| Chen et al., arXiv 2604.18880 | C | 초록 |
| Gao et al., arXiv 2603.22344 | C | 초록 |
| Onweller et al., arXiv 2605.06635 | C·D | 초록 |
| Goo et al., arXiv 2607.20527 | C | 초록 |
| Williams, arXiv 2607.09932 | C | 초록 |
| Miyai et al., arXiv 2604.01128 | C | 초록 |
| Zabaleta & Lin, SciLitBench, arXiv 2609.05505 | C | 초록 |
| Oami et al., Front Digit Health, doi 10.3389/fdgth.2026.1799623 | C | 본문 grep |
| Figalová et al., arXiv 2608.26885 | C·D | 초록 |
| Shafqat et al., arXiv 2608.12741 | C | 초록 |
| Lahlou et al., arXiv 2603.20235 | C | 초록 |
| Chen et al., Judging Is Not Enumerating, arXiv 2608.01000 | D | 초록 |
| Xiong et al., AutoResearchBench, arXiv 2604.25256 | C | 초록 |
| Belem et al., arXiv 2606.07951 | C | 초록 |
| Tan & D'Souza, arXiv 2602.10881 | C | 초록 |
| Yang et al., arXiv 2606.32029 | C | 초록 |
| Kohli, arXiv 2605.29800 | D | 초록 |
| Kim et al., arXiv 2605.20668 | C | 초록 |
| Norman et al., arXiv 2606.19544 | C | 초록 |
| Peng et al., RuVerBench, arXiv 2606.29920 | D | 초록 |
| Wang et al., Verification Horizon, arXiv 2606.26300 | D | 초록 |
| Nguyen et al., arXiv 2606.19749 | C | 초록 |
| DeepFact, arXiv 2603.05912 | C | 초록 |
| Cho & Sun, arXiv 2605.12947 | D | 초록 |
| Vivekanantha et al., KSSTA 34(8), PMC13418397 | D | PMC grep |
| CiteTracer, arXiv 2605.08583 | C | 초록 |
| CiteCheck, arXiv 2605.27700 | C | 초록 |
| CiteAudit, arXiv 2602.23452 | C·D | 초록 + HTML v1(벤치 크기만) |
| Charlotin, AI Hallucination Cases(2046건, 2026-09-21) | D | grep |
