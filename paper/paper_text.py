"""The text of the paper. Every number comes from numbers.json (paper_numbers.py)."""

REPO = "https://github.com/eungyun-im/llm-testcase-review"
FROZEN_COMMIT = "b1b7f4f"  # the design v2 as amended; the run starts from this commit

REFERENCES = [
    '1) ISO 26262-6:2018, "Road vehicles - Functional safety - Part 6: Product development at the software level", International Organization for Standardization, 2018.',
    '2) K.-W. Shin and D.-J. Lim, "Model-based automatic test case generation for automotive embedded software testing", International Journal of Automotive Technology, Vol. 19, No. 1, pp. 107-119, 2018.',
    '3) E. T. Barr, M. Harman, P. McMinn, M. Shahbaz and S. Yoo, "The oracle problem in software testing: a survey", IEEE Transactions on Software Engineering, Vol. 41, No. 5, pp. 507-525, 2015.',
    '4) Y. Jia and M. Harman, "An analysis and survey of the development of mutation testing", IEEE Transactions on Software Engineering, Vol. 37, No. 5, pp. 649-678, 2011.',
    '5) R. Just, D. Jalali, L. Inozemtseva, M. D. Ernst, R. Holmes and G. Fraser, "Are mutants a valid substitute for real faults in software testing?", Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering, pp. 654-665, 2014.',
    '6) M. Schäfer, S. Nadi, A. Eghbali and F. Tip, "An empirical evaluation of using large language models for automated unit test generation", IEEE Transactions on Software Engineering, Vol. 50, No. 1, pp. 85-105, 2024.',
    '7) J. Wang, Y. Huang, C. Chen, Z. Liu, S. Wang and Q. Wang, "Software testing with large language models: survey, landscape, and vision", IEEE Transactions on Software Engineering, Vol. 50, No. 4, pp. 911-936, 2024.',
    '8) M. Abboush, A. Hatahet and A. Rausch, "LLMs-powered real-time fault injection: an approach toward intelligent fault test cases generation", arXiv:2511.19132, 2025.',
    '9) A. M. Dakhel, A. Nikanjam, V. Majdinasab, F. Khomh and M. C. Desmarais, "Effective test generation using pre-trained large language models and mutation testing", Information and Software Technology, Vol. 171, Article 107468, 2024.',
    '10) X. Wang, J. Wei, D. Schuurmans, Q. Le, E. Chi, S. Narang, A. Chowdhery and D. Zhou, "Self-consistency improves chain of thought reasoning in language models", Proceedings of the International Conference on Learning Representations (ICLR), 2023.',
    '11) A. Madaan et al., "Self-refine: iterative refinement with self-feedback", arXiv:2303.17651, 2023.',
    '12) A. Arcuri and L. Briand, "A practical guide for using statistical tests to assess randomized algorithms in software engineering", Proceedings of the 33rd International Conference on Software Engineering, pp. 1-10, 2011.',
    '13) A. Vargha and H. D. Delaney, "A critique and improvement of the CL common language effect size statistics of McGraw and Wong", Journal of Educational and Behavioral Statistics, Vol. 25, No. 2, pp. 101-132, 2000.',
    '14) A. Yang et al., "Qwen2.5 technical report", arXiv:2412.15115, 2024.',
]


def pc(x, digits=0):
    return f"{x * 100:.{digits}f}"


def pval(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


class N:
    """Accessors over numbers.json."""

    def __init__(self, numbers):
        self.models = {m["model"]: m for m in numbers["models"]}

    def m(self, name):
        return self.models.get(name)

    def mean(self, name, cond, metric="error_rate"):
        return self.models[name]["conditions"][cond][metric]["mean"]

    def sd(self, name, cond, metric="error_rate"):
        return self.models[name]["conditions"][cond][metric]["sd"]

    def msd(self, name, cond, metric="error_rate"):
        return f"{pc(self.mean(name, cond, metric))}±{pc(self.sd(name, cond, metric))}"

    def reps(self, name, cond="FR-ordered"):
        return self.models[name]["conditions"][cond]["error_rate"]["n"]

    def cmp(self, name, key):
        return self.models[name]["comparisons"][key]

    def vote(self, name, cond, key):
        return self.models[name]["votes"][cond][key]


def failures_text(n, reps, models):
    """Sentence on repetitions left out because a run failed (output cut off at the length limit)."""
    parts = []
    for name, label in models:
        m = n.m(name)
        if not m:
            continue
        lost = [(key, reps - c["error_rate"]["n"]) for key, c in m["conditions"].items() if c["error_rate"]["n"] < reps]
        if lost:
            what = ", ".join(f"{key} {count}회" for key, count in lost)
            parts.append(f"{label} 모델에서는 출력이 최대 길이에서 잘려 실패한 실행({what})이 분석에서 빠졌다. ")
    return "".join(parts)


def compose(numbers):
    n = N(numbers)
    M7 = "qwen2.5:7b"
    M3 = "qwen2.5:3b"
    M14 = "qwen2.5:14b"
    has3, has14 = n.m(M3) is not None, n.m(M14) is not None
    h1, h2 = n.cmp(M7, "H1"), n.cmp(M7, "H2")
    target = n.m(M7)["target"]
    equal = n.m(M7).get("equal_size", {})
    reps = n.reps(M7)

    abstract = (
        "Test cases written by large language models (LLMs) are only as useful as their expected results. For safety-related automotive software "
        "a wrong expected result either fails a correct implementation or lets a defect pass. We measure the share of wrong expected results in LLM-written "
        "test cases for an automatic emergency braking (AEB) decision function by executing them against a reference implementation, and find that the "
        f"expected result, not the choice of inputs, is where a {M7.split(':')[1].upper()} model fails: {pc(n.mean(M7, 'B1'))} % of its expected results were wrong, "
        f"and a vote of the same model on the raw input values left this at {pc(n.mean(M7, 'FR-self'))} %. We propose a procedure that separates the two parts "
        "of a test case. The model only adds test inputs for gaps found by automatic checks. The expected result of each test is the majority of three votes "
        "in which a program has already decided the atomic conditions of the requirements, and the model applies the requirements to them in a given order, "
        f"one test per query. Over {reps} repetitions the share of wrong expected results fell from {pc(n.mean(M7, 'B1'))} % to {pc(n.mean(M7, 'FR-ordered'))} % "
        f"(paired Wilcoxon, {pval(h2['p'])}), and the single votes were right in {pc(n.vote(M7, 'FR-ordered', 'single_right'))} % of the cases. "
        + (f"The effect depends on the capability of the model: for a {M3.split(':')[1].upper()} model, whose votes were right in only "
           f"{pc(n.vote(M3, 'FR-ordered', 'single_right'))} % of the cases, the error rate was {pc(n.mean(M3, 'B1'))} % without and "
           f"{pc(n.mean(M3, 'FR-ordered'))} % with the procedure. " if has3 and 'FR-ordered' in n.m(M3)['votes'] else "")
        + f"Defect detection rose from {pc(n.mean(M7, 'B1', 'detection_mutants'))} % to {pc(n.mean(M7, 'FR-ordered', 'detection_mutants'))} % of mutants, "
          "but this comes from the added inputs, not from the vote. The design, code and data are public."
    )

    blocks = []
    add = blocks.append

    add(("h1", "1. 서 론"))
    add(("p", "ISO 26262-6은 차량 소프트웨어의 단위 검증에 요구사항 기반 테스트와 경계값 분석을 권고한다.[[1]] 테스트 케이스 설계는 사람의 시간이 많이 드는 "
              "작업이어서, 대규모 언어 모델(LLM)로 요구사항에서 테스트를 생성하려는 연구가 빠르게 늘고 있다.[[6,7]] 자동차 분야에서도 기능 안전 요구사항에서 "
              "결함 주입 테스트를 생성하려는 시도가 보고되었고,[[8]] 임베디드 소프트웨어의 테스트 케이스 자동 생성은 이 학회의 영문 논문집에서도 다루어졌다.[[2]]"))
    add(("p", "테스트 케이스는 입력과 기대 결과로 이루어진다. 기대 결과가 틀린 테스트는 올바른 코드를 불합격시키거나 결함을 통과시킨다. 무엇이 올바른 출력인지를 "
              "정하는 이 문제는 테스트 오라클 문제로 알려져 있다.[[3]] 기존의 LLM 테스트 생성 연구는 주로 생성된 테스트가 실행되는지, 얼마나 많은 코드를 "
              "실행하는지, 변이를 얼마나 잡는지를 평가한다.[[6,9]] 그러나 변이 점수와 같은 지표는 기대 결과가 맞다는 가정 위에서만 의미가 있다.[[4,5]] "
              "모델이 자신의 출력을 다시 검토하는 자기 개선[[11]]이나 여러 번 풀어 다수결을 취하는 방식[[10]]은 모델이 체계적으로 틀리는 문제에서 같은 오류를 "
              "반복할 수 있다."))
    add(("p", "본 연구는 AEB 판단 함수를 대상으로 (1) LLM이 쓴 테스트의 기대 결과 오류를 기준 구현에 대한 실행으로 측정하고, (2) 오류가 입력 선택이 아니라 "
              "기대 결과에 있음을 보이며, (3) 입력 생성과 기대 결과 결정을 분리하고 요구사항의 원자 조건을 프로그램이 판정해 주는 조건 기반 투표로 "
              "기대 결과의 오류를 줄일 수 있는지, 그리고 그 효과가 모델의 크기에 어떻게 달라지는지를 실험한다."))

    add(("h1", "2. 연구 방법"))
    add(("h2", "2.1 대상 함수와 구조화된 명세"))
    add(("p", "대상은 단순화한 AEB 판단 함수이다. 입력은 속도(km/h), 장애물 거리(m, 없을 수 있음), 센서 데이터 경과 시간(ms)이고, 출력은 BRAKE, NO_ACTION, "
              "FAULT 중 하나이다. 요구사항은 4개이며 적용 순서(속도 범위 오류, 센서 데이터 오래됨, 제동 조건 순)가 있다. 자연어 요구사항에 출력 값을 포함하지 않는 "
              "구조를 덧붙인다. 경계 5개(15개 값: 임계값과 그 전후 한 단계), 원자 조건 6개(예: 속도 30 km/h 이상), 입력 분류 7개(요구사항이 다르게 "
              "다루는 조건 조합), 그리고 요구사항의 적용 순서이다."))
    add(("h2", "2.2 입력 생성: 추가만 하는 보완"))
    add(("p", "출발점은 모델이 명세를 받아 한 번에 생성한 테스트 세트(B1)이다. 이후 최대 3라운드 동안 세 가지 자동 검사가 빈 곳을 찾는다. 어떤 테스트도 쓰지 않은 "
              "경계 값, 테스트가 없는 입력 분류, 어떤 테스트 입력으로도 원래 코드와 구분되지 않는 변이이다. 모델은 이 목록을 받아 새 테스트만 내놓고, 기존 테스트는 "
              "시스템이 보관하며 다시 쓰이지 않는다. 변이는 절반(13개)만 피드백에 쓰고 나머지 절반(12개)은 평가에만 쓴다."))
    add(("h2", "2.3 기대 결과: 조건 기반 투표"))
    add(("p", "기대 결과는 마지막에 한 번 정한다. 프로그램이 각 테스트 입력에 대해 원자 조건 6개를 참 또는 거짓으로 판정하고, 모델은 입력 수치를 보지 않고 판정 결과와 "
              "요구사항만 받는다. 모델은 지정된 순서로 요구사항을 적용해 출력을 답하며, 질문 하나에 테스트 하나를 묻는다. 같은 질문을 3번 하고 다수결을 해당 "
              "테스트의 기대 결과로 기록한다. 투표의 샘플링 온도는 0.3이다(생성은 기본값). 정답 구현은 이 어디에도 쓰지 않으며 평가에만 쓴다.(Fig. 1)"))
    add(("fig", "fig1.png", "Procedure: the model adds inputs, the program decides the conditions, the vote decides the expected results"))

    add(("h1", "3. 실험"))
    add(("h2", "3.1 설정"))
    models_text = "Qwen2.5 3B, 7B" + (", 14B" if has14 else "")
    add(("p", f"모델은 {models_text}[[14]]을 Ollama로 로컬에서 실행하였다(4비트 양자화, 샘플링은 서버 기본값, 투표만 0.3). 조건은 7가지이다. "
              "B0(요구사항만), B1(명세 포함), 추가만 하고 기대 결과는 모델이 쓴 그대로 둔 조건(Extended only), 입력 수치를 보고 투표하는 조건(Raw-value vote), "
              "라운드마다 모델이 테스트 세트를 다시 쓰는 조건(Rewrite loop), 조건 판정을 주되 40개를 한 번에 묻는 조건(Grounded vote), 그리고 제안 방법(Proposed)이다. "
              f"반복 횟수는 조건당 {reps}회이며 반복마다 같은 B1에서 출발한다."))
    add(("p", "평가는 모두 실행으로 한다. 오답률은 기대 결과가 기준 구현의 출력과 다른 테스트의 비율이다. 결함 검출률은 올바른 테스트 중 하나라도 실패하는 결함 버전의 비율이며, "
              "수작업으로 심은 결함 7개와 평가용 변이 12개에 대해 각각 구한다. 비용은 모델 호출 수이다. 짝지은 비교는 Wilcoxon 부호 순위 검정,[[12]] 효과 크기는 "
              "Vargha-Delaney A12,[[13]] 다중 비교는 Holm 보정을 쓴다."))
    add(("p", f"가설과 목표는 실행 전에 고정하여 공개하였다.(저장소 커밋 {FROZEN_COMMIT}, {REPO}) H1: 제안 방법의 오답률은 Grounded vote보다 낮다. "
              f"H2: 제안 방법의 오답률은 B1보다 낮다. T: 제안 방법의 평균 오답률은 {pc(target['limit'])} % 이하이다. H1, H2는 Holm으로 보정하고 T는 목표로서 "
              "충족 여부만 보고한다. 이 설계는 소형 모델 파일럿 3회와 설계를 고정한 확인 실험 1회의 결과를 반영한 것이며, 해당 실험은 저장소에 기록되어 있다."))
    add(("h2", "3.2 결과"))
    add(("p", f"{M7.split(':')[1].upper()} 모델의 결과를 Table 1과 Fig. 2에 보인다. B1의 오답률은 {n.msd(M7, 'B1')} %였고 제안 방법은 {n.msd(M7, 'FR-ordered')} %였다. "
              f"제안 방법은 {h2['pairs']}번의 반복 중 {h2['lower_in']}번에서 B1보다 낮았다({pval(h2['p'])}, Holm 보정 후 {pval(h2['p_holm'])}, A12 = {h2['a12']:.2f}). "
              f"목표 T(평균 {pc(target['limit'])} % 이하)는 평균 {pc(target['mean'], 1)} %, 가장 나쁜 반복 {pc(target['worst'])} %로 "
              + ("충족되었다." if target["met"] else "충족되지 못했다.")))
    add(("table", 1, "Results of the 7B model (mean of repetitions; error: wrong expected results, seeded and mutant: defect detection)", ["Condition", "Error %", "Seeded %", "Mutant %", "Calls"],
         [[label, pc(n.mean(M7, key)), pc(n.mean(M7, key, "detection_seeded")), pc(n.mean(M7, key, "detection_mutants")), f"{n.mean(M7, key, 'llm_calls'):.0f}"]
          for key, label in (("B1", "B1 (start)"), ("FR-cross", "Extended only"), ("FR-self", "Raw-value vote"), ("FR-rewrite", "Rewrite loop"),
                             ("FR", "Grounded vote"), ("FR-ordered", "Proposed"))
          if key in n.m(M7)["conditions"]],
         [1500, 680, 680, 700, 680], (5,)))
    add(("fig", "fig2.png", "Share of wrong expected results per repetition (7B model; bar: mean)"))
    cross = n.m(M7)["conditions"].get("FR-cross")
    selfv = n.m(M7)["conditions"].get("FR-self")
    rew = n.m(M7)["conditions"].get("FR-rewrite")
    add(("p", f"오류의 원인은 입력이 아니라 기대 결과에 있다. 기대 결과를 모델이 쓴 그대로 둔 조건({pc(cross['error_rate']['mean'])} %)과 입력 수치를 보고 투표한 조건"
              f"({pc(selfv['error_rate']['mean'])} %)은 B1({pc(n.mean(M7, 'B1'))} %)에서 개선되지 않았다. 투표 한 번의 정답률이 {pc(n.vote(M7, 'FR-self', 'single_right'))} %에 그쳐서, "
              "세 번 모아도 같은 오류가 반복되어 다수결이 잘못된 값을 확정하였다. 조건 판정을 주면 40개를 한 번에 물어도 "
              f"{pc(n.vote(M7, 'FR', 'single_right'))} %로 오르고, 한 번에 하나씩 순서를 주면 {pc(n.vote(M7, 'FR-ordered', 'single_right'))} %가 된다. "
              f"같은 검사 결과를 받고도 모델이 세트를 다시 쓰게 한 조건은 {pc(rew['error_rate']['mean'])} %로 개선되지 않았고 호출이 {rew['llm_calls']['mean']:.0f}회로 "
              "가장 많았다. 방법의 오답률은 결국 투표의 오답률과 같다."))
    es = equal.get("FR-ordered"), equal.get("B1")
    ext = n.m(M7)["conditions"]["FR-cross"]
    add(("p", f"결함 검출률은 제안 방법이 수작업 결함 {pc(n.mean(M7, 'FR-ordered', 'detection_seeded'))} %, 변이 "
              f"{pc(n.mean(M7, 'FR-ordered', 'detection_mutants'))} %로 B1({pc(n.mean(M7, 'B1', 'detection_seeded'))} %, {pc(n.mean(M7, 'B1', 'detection_mutants'))} %)보다 "
              "높았다. 그러나 이 향상은 투표가 아니라 입력 보완 단계에서 나온다. 기대 결과를 고치지 않은 Extended only도 "
              f"{pc(ext['detection_seeded']['mean'])} %, {pc(ext['detection_mutants']['mean'])} %이다. "
              + (f"테스트 수를 B1과 같게 맞추면 제안 방법의 검출률은 {pc(es[0]['seeded'])} %, {pc(es[0]['mutants'])} %이고 B1은 {pc(es[1]['seeded'])} %, {pc(es[1]['mutants'])} %이다. " if es[0] and es[1] else "")
              + f"비용은 호출 수로 B1 1회, 제안 방법 {n.mean(M7, 'FR-ordered', 'llm_calls'):.0f}회이다(투표가 테스트마다 3회). "
              "틀린 기대 결과를 줄이는 일과 결함을 더 찾는 일은 서로 다른 단계가 담당한다."))

    add(("h2", "3.3 모델 크기의 영향"))
    rows, labels = [], []
    for name, label in ((M3, "3B"), (M7, "7B"), (M14, "14B")):
        m = n.m(name)
        if not m or "FR-ordered" not in m["votes"]:
            continue
        rows.append([label, pc(n.mean(name, "B1")), pc(n.mean(name, "FR-ordered")), pc(n.vote(name, "FR-ordered", "single_right")),
                     f"{pc(n.vote(name, 'FR-ordered', 'unanimous_share'))}/{pc(n.vote(name, 'FR-ordered', 'unanimous_right'))}"])
    add(("p", "모델 크기별 결과를 Table 2와 Fig. 3에 보인다. 제안 방법의 효과는 모델이 요구사항을 판정된 조건에 적용할 수 있는지에 달려 있다. "
              + (f"3B 모델은 투표가 {pc(n.vote(M3, 'FR-ordered', 'single_right'))} %만 맞았고, 오답률은 B1 {pc(n.mean(M3, 'B1'))} %에서 {pc(n.mean(M3, 'FR-ordered'))} %로 "
                 f"낮아졌으나 유의하지 않았고({pval(n.cmp(M3, 'H2')['p'])}, {n.cmp(M3, 'H2')['pairs']}번 중 {n.cmp(M3, 'H2')['lower_in']}번) 목표 T도 충족하지 못했다. "
                 "세 번의 투표가 항상 일치하여 다수결은 정정 효과가 없었다. " if has3 and 'FR-ordered' in n.m(M3)['votes'] else "")
              + (f"14B 모델은 B1 {pc(n.mean(M14, 'B1'))} %에서 {pc(n.mean(M14, 'FR-ordered'))} %로 "
                 f"변하였다. " if has14 and 'FR-ordered' in n.m(M14)['votes'] else "")))
    add(("table", 2, "Effect by model (error rate of B1 and of the proposed method, share of single votes that are right, share of tests on which all votes agree / share of those that are right)",
         ["Model", "B1 %", "Prop. %", "Vote %", "Agree/right %"], rows, [650, 700, 800, 780, 1300]))
    add(("fig", "fig3.png", "Share of single votes that are right, by model and way of voting"))

    add(("h2", "3.4 논의와 한계"))
    unanimous = n.vote(M7, "FR-ordered", "unanimous_share")
    unanimous_right = n.vote(M7, "FR-ordered", "unanimous_right")
    add(("p", f"세 표가 모두 일치한 테스트는 {pc(unanimous)} %이고 그 정답률은 {pc(unanimous_right)} %이다. 일치하지 않은 테스트를 사람이 확인하도록 분리하면 "
              "자동으로 확정하는 부분의 신뢰도를 더 높일 수 있다. 이 결과는 구조화 비용을 전제로 한다. 조건 6개, 입력 분류 7개, 적용 순서를 사람이 명세에 적어야 하며, "
              "이 구조화가 더 복잡한 요구사항에서 어떻게 늘어나는지는 확인하지 못했다."))
    add(("p", "한계는 다음과 같다. 대상은 상태가 없는 함수 1개이며 시간 순서가 있는 요구사항에는 적용하지 않았다. 모델은 Qwen2.5 계열의 두 크기(3B, 7B)이고 더 큰 모델과 상용 모델은 시험하지 않았다. "
              + failures_text(n, reps, ((M3, "3B"), (M7, "7B")))
              + "명세와 기준 구현을 같은 사람이 작성하였고, 투표의 온도와 질문 방식은 앞선 실험의 테스트로 정하였다. 사람이 설계한 테스트와의 비교는 포함하지 않았다. "
              "파서 규칙은 파일럿 모델의 출력을 보고 정하였다."))

    add(("h1", "4. 결 론"))
    add(("p", "LLM이 쓴 테스트의 오류는 입력 선택보다 기대 결과에 있었고, 이를 줄이는 방법을 실험하였다."))
    add(("item", f"1) 7B 모델이 쓴 AEB 테스트의 기대 결과 {pc(n.mean(M7, 'B1'))} %가 틀렸고, 같은 모델이 입력 수치를 보고 다시 투표해도 {pc(n.mean(M7, 'FR-self'))} %가 틀렸다."))
    add(("item", f"2) 프로그램이 요구사항의 원자 조건을 판정하고 모델이 지정된 순서로 한 번에 하나씩 적용하는 투표를 쓰자 오답률이 {pc(n.mean(M7, 'FR-ordered'))} %로 낮아졌다."))
    add(("item", "3) 방법의 오답률은 투표의 오답률과 같고, 그 효과는 모델이 규칙을 적용할 수 있을 때에만 나타났다." + (f" 3B 모델에서는 오답률이 {pc(n.mean(M3, 'FR-ordered'))} %에 머물러 목표에 이르지 못했다." if has3 else "")))
    add(("item", "4) 결함 검출률의 향상은 투표가 아니라 입력 보완 단계에서 나왔다. 사람이 설계한 기준선, 시간 순서가 있는 대상, 더 큰 모델은 후속 과제이다."))

    add(("note", "후기 : 이 연구의 코드, 실험 실행, 원고 초안의 작성에 AI 도구(Anthropic Claude)를 사용하였으며, 저자가 내용을 검토하였다. 설계, 코드, 원자료는 위 저장소에 공개되어 있다."))
    add(("references", REFERENCES))

    return {
        "title_ko": "조건 기반 투표를 이용한 LLM 생성 테스트 케이스의 기대 결과 정확도 향상",
        "authors_ko": [("임은균", "*1)")],
        "affiliations_ko": ["국민대학교 자동차공학과"],
        "title_en": "Improving the Expected-Result Accuracy of LLM-Generated Test Cases by Condition-Grounded Voting",
        "authors_en": [("Eungyun Im", "*1)")],
        "affiliations_en": ["Department of Automotive Engineering, Kookmin University, 77, Jeongneung-ro, Seongbuk-gu, Seoul 02707, Korea"],
        "email": "dladmsrbs12350@kookmin.ac.kr",
        "abstract": abstract,
        "keywords": "Large language model(대규모 언어 모델), Test oracle(테스트 오라클), Software testing(소프트웨어 테스트), "
                    "Mutation testing(변이 테스트), Automotive software(자동차 소프트웨어), ISO 26262",
        "blocks": blocks,
    }
