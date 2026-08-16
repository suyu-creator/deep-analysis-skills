---
name: red-team-the-plan
description: Pressure-test a plan, proposal, pitch, strategy, or decision by role-playing its adversaries — attacking it from the perspectives of a smart competitor, an angry customer, a skeptical CFO, a lazy/overloaded engineer, a regulator, and an investor — to surface the attacks it can't answer BEFORE it faces them for real. Use this skill when preparing to present to a board, investors, or leadership; before a product or pricing launch; when a proposal needs to survive hostile scrutiny; when someone says "poke holes in this", "what will they ask", "stress-test this", "play devil's advocate", "will this survive the board", or "prep me for the hard questions". Distinct from grill-me (general adversarial questioning) and pre-mortem (imagined failure): red-team assigns specific ADVERSARY ROLES, each of which attacks from its own incentives, so you find the attack vectors a single reviewer's blind spots would miss.
---

# Red-Team the Plan

> ⚠️ **定位(deep-analysis 集成)**:对抗是**可选环节**,非闸门。用户在闸门 2 确认后 decide 是否跑;可行性判断已并入闸门 2 的「可行性+风险小结」。跳过对抗则无攻击面,reporter 交叉环节自动降级为仅遗漏清单。

Your plan will eventually meet people who *want* it to fail, or who simply have different incentives than you: a competitor who'll counter it, a customer who feels wronged by it, a CFO who distrusts the numbers, an engineer who has to build it and is already underwater, a regulator who reads it uncharitably, an investor deciding whether to fund it. Each attacks from a different angle. **Better that they attack it here, in a dry run, than in the room that matters.**

Red-teaming is the structured version of "what will they throw at me?" — done by deliberately *becoming* each adversary instead of defending your own plan.

## The one thing that actually matters

The valuable output is the **list of attacks the plan currently has NO answer for.** Attacks you can already rebut are reassurance; attacks that land are the product. Every unanswered attack becomes a thing to fix, an objection to pre-empt in the deck, or a slide you'd better prepare — *before* the real audience finds it. A red-team that produces only attacks you can comfortably swat was too gentle; push each role until it draws blood, then write down where it drew blood.

## Why roles, not just "criticize it"

A single critic has a single set of blind spots. Generic criticism clusters around whatever that person happens to care about. Assigning **distinct adversary roles with distinct incentives** forces coverage of attack surfaces a lone reviewer would never think of — the CFO never asks the questions the angry customer asks, and neither thinks like the competitor. The roles are a checklist that defeats your own blind spots.

## The six adversaries

Run the plan past each. For each, *adopt their incentives fully* and attack — don't pull punches to protect your plan.

### 1. The smart competitor
Incentive: beat you. Attacks:
- "When you do this, here's exactly how I counter — and I can do it faster/cheaper because ___."
- "This is easy for me to copy. What's your moat after I do?"
- "You just told the market your strategy. I'll position against it like this."
- "You're picking a fight on the one dimension I'm strongest."

### 2. The angry / churning customer
Incentive: their own outcome, not yours. Attacks:
- "This is worse for me than what I have now, because ___."
- "You're making me change my behavior/workflow and I won't bother."
- "I don't trust you to do this — last time ___."
- "The price went up / the thing I relied on went away. I'm leaving."
- "This solves a problem I don't actually have."

### 3. The skeptical CFO
Incentive: protect cash, distrust optimism. Attacks:
- "Where does this number come from? Walk me through it bottoms-up."
- "What's the CAC, the payback period, the unit economics at scale — not the hope, the math?"
- "What does this cost if it only half-works? What's the downside case?"
- "What are we NOT funding because we funded this?"
- "Your forecast assumes a hockey stick. Why this quarter and not the last four?"

### 4. The overloaded engineer / operator who must build it
Incentive: ship without dying; distrust hand-wavy scope. Attacks:
- "The hard part isn't the part you planned for — it's ___, and that's weeks not days."
- "This depends on [system/team] that is already a mess / already overcommitted."
- "Who maintains this after launch? You've designed a thing that needs a babysitter."
- "Your timeline has no slack and assumes nothing else breaks. It will."
- "This is technically possible and operationally insane."

### 5. The regulator / compliance / legal reviewer
Incentive: read it uncharitably, assume worst case. Attacks:
- "Are you allowed to do this? Show me the rule that permits it."
- "What happens when you're wrong about someone publicly? Who sues?"
- "Where's the data coming from, and do you have the right to use it that way?"
- "This is fine until it's at scale and visible — then it's a target."
- "What's your answer when a regulator/journalist asks you this on the record?"

### 6. The investor deciding whether to back it
Incentive: returns and downside-protection; pattern-matches to failures. Attacks:
- "Why now? Why you? Why hasn't someone bigger already done this?"
- "What has to be true for this to be a 10x, not a 1.2x?"
- "What's the single thing most likely to kill this, and what's your plan for it?"
- "I've seen this movie before and it ended badly because ___. How are you different?"
- "Your TAM math is top-down storytelling. Show me bottoms-up."

## The method

1. **State the plan in 3–5 lines** so each adversary attacks the same target. Ambiguity lets you dodge; pin the plan first.
2. **Run each role in turn.** Fully inhabit the incentive. Generate 3–6 sharp attacks per role — specific, not generic ("your CAC assumption of 500 is fantasy because acquisition in this segment runs 2–3k," not "costs might be high").
3. **For each attack, force an honest verdict:** ✅ we have a solid answer (write it) / 🟨 weak answer (note the gap) / 🔴 no answer (this is a finding).
4. **Collect every 🔴 and 🟨 into the "unanswered attacks" list** — ranked by how likely the real audience is to raise it × how badly it lands.
4b. ⚠️ **Every 🔴 attack → look up how mature open-source projects solve it** (via `search_github` / `read_github_file`, or `gh search repos` / `curl` when MCP is down). Pull the concrete counter / architecture / fallback into the response column, annotated with `repo+file`; only fall back to inference when no implementation exists. 🟨 attacks may be answered from reasoning but must be labeled 🟡 推理. This is "after surfacing the attack, re-check GitHub for the fix" — don't write a first-pass answer and call it done.
#* 方案规则(必须给方案,两级标注): 🔴/🟨 攻击的 Response 列每条必须给出 1 主案 + 1-2 备选,不留空。方案标级:🟢 实证 = 查过 GitHub,带 repo@文件:行号;🟡 推理 = 未查,基于经验(注明原因)。🔴 攻击(杀伤力最高)必须 🟢,只给 🟡 = 不合格,立即补查;🟨 允许 🟡 推理。判据:该攻击若真实发生,后果要投入(钱/时间/承诺)吗?是→必查;否→可推理。

5. **Decide a response for each:** fix the plan, pre-empt it in the materials, prepare a rebuttal, or accept-and-disclose it. Walking into the room with a prepared answer to your three worst attacks is the deliverable.

## What good output looks like

**Unanswered / weak attacks, ranked:**

| # | Adversary | Attack | Verdict | Response |
|---|---|---|---|---|
| 1 | CFO | "TrustScore pricing assumes 200k/yr but you have zero paying brokers — that's a wish, not a forecast" | 🔴 none | Get 3 paid LOIs before the board meeting; reframe slide as "design-partner validated" |
| 2 | Competitor | "A bigger review site copies TrustScore in a quarter; what's left?" | 🟨 weak | Build the moat slide: proprietary regulator data + Sentinel pipeline, not the score itself |
| 3 | Regulator | "You're publishing negative trust scores on named firms — who's liable when you're wrong?" | 🔴 none | Lock the right-of-reply + legal-review gate; prepare the "facts-layer only until consent" answer |
| 4 | Engineer | "Scoring 44k entities credibly needs the match pipeline working; it's at 2%" | 🟨 weak | De-scope launch to the verticals where match rate is already high |

Four attacks you couldn't answer, now with a plan, beats a confident rehearsal that gets ambushed live.

## Running it well

- **Inhabit, don't sympathize.** The failure mode is role-playing a *polite* adversary. Real CFOs aren't nice about your numbers. If the attacks feel uncomfortable, it's working.
- **Specific beats generic.** "Costs might be higher" is useless. "Your 500 THB CAC is 4–6x too low for this segment, here's why" is a finding. Push every attack to a concrete number or mechanism.
- **Use the adversary the plan most fears.** If you flinch at running the regulator role, that's exactly the one to run hardest.
- **A friendly outside human amplifies it.** If you can get one real person to play one role for 15 minutes, do — but the role-checklist alone already beats unstructured "any feedback?"

## Pitfalls

- **Defending instead of attacking.** The instinct is to justify the plan as each objection arises. Don't — generate the *full* attack list first, in-character, then assess. Mixing defense into generation blunts the attacks.
- **Stopping at attacks you can answer.** Those are the comfortable ones. The exercise only pays off when it surfaces an attack you *can't* answer — that's the whole point, not a failure of the plan.
- **Skipping a role because "it doesn't apply."** If a role genuinely doesn't apply (no regulator in your world), say so explicitly — but check twice, because "regulation doesn't affect us" is itself a classic 🔴.
- **Confusing it with pre-mortem / grill-me.** Pre-mortem imagines the plan already dead and asks why. grill-me interrogates the idea's internal logic. Red-team simulates *specific external adversaries* attacking from their incentives. For a high-stakes pitch, run all three: grill-me to harden the logic, assumption-audit to test the beliefs, red-team to survive the room.
- **No response column.** A list of attacks with no decided response is just anxiety with extra steps. Each finding needs fix / pre-empt / rebut / accept.

## When to use

Before any high-stakes, adversarial-audience moment: board meetings, investor pitches, pricing/launch decisions, partnership proposals, anything where smart people with different incentives will scrutinize your plan. Overkill for low-stakes internal decisions with a friendly audience.
