SCORE_EMOJI = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
VERDICT_EMOJI = {"PASS": "✅", "CONCERN": "⚠️", "FAIL": "❌"}
SEVERITY_EMOJI = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def build_markdown_report(
    trust_brief: dict,
    domain_results: list[dict],
    holistic: dict,
) -> str:
    sections = []

    # ── Repo Overview ──────────────────────────────────────────────────────
    sections.append("## Repo Overview\n")
    sections.append(f"**Repository:** `{trust_brief['repo']}`  ")
    sections.append(f"**Tech Stack:** {', '.join(trust_brief['tech_stack'])}  ")
    sections.append(f"**Agent Architecture:** {trust_brief['agent_architecture']}\n")

    if trust_brief["safety_mechanisms_observed"]:
        sections.append("**Safety mechanisms observed:**")
        for m in trust_brief["safety_mechanisms_observed"]:
            sections.append(f"- {m}")
        sections.append("")

    if trust_brief["notable_absences"]:
        sections.append("**Notable absences:**")
        for a in trust_brief["notable_absences"]:
            sections.append(f"- {a}")
        sections.append("")

    # ── Domain Scorecards ──────────────────────────────────────────────────
    sections.append("## Domain Scorecards\n")
    sections.append("| Domain | Score | Summary |")
    sections.append("|--------|-------|---------|")
    for dr in domain_results:
        score = dr["overall_domain_score"]
        emoji = SCORE_EMOJI.get(score, score)
        sections.append(f"| {dr['domain']} | {emoji} {score} | {dr['domain_summary']} |")
    sections.append("")

    # ── Risk Detail ────────────────────────────────────────────────────────
    sections.append("## Risk Detail\n")
    for dr in domain_results:
        sections.append(f"### {dr['domain']}\n")
        sorted_risks = sorted(
            dr["risks_assessed"],
            key=lambda r: (SEVERITY_ORDER.get(r["severity"], 99), r["verdict"] == "PASS"),
        )
        for risk in sorted_risks:
            emoji = VERDICT_EMOJI.get(risk["verdict"], risk["verdict"])
            sections.append(f"**{emoji} {risk['risk']}** ({risk['severity']})")
            sections.append(f"> {risk['evidence']}\n")

    # ── Compound Risks ─────────────────────────────────────────────────────
    sections.append("## Compound Risks\n")
    if holistic["compound_risks"]:
        for cr in holistic["compound_risks"]:
            combo = " + ".join(cr["risk_combination"])
            sections.append(f"**{SEVERITY_EMOJI.get(cr['severity'], cr['severity'])} {combo}** ({cr['severity']})")
            sections.append(f"> {cr['emergent_concern']}\n")
    else:
        sections.append("No significant compound risks identified.\n")

    # ── Top Recommendations ────────────────────────────────────────────────
    sections.append("## Top Recommendations\n")
    for i, rec in enumerate(holistic["top_3_recommendations"], 1):
        sections.append(f"{i}. {rec}")
    sections.append("")

    # ── Overall Verdict ────────────────────────────────────────────────────
    verdict = holistic["overall_verdict"]
    emoji = SCORE_EMOJI.get(verdict, verdict)
    sections.append("## Overall Verdict\n")
    sections.append(f"# {emoji} {verdict}")

    return "\n".join(sections)


def build_json_report(
    trust_brief: dict,
    domain_results: list[dict],
    holistic: dict,
) -> dict:
    return {
        "trust_brief": trust_brief,
        "domain_results": domain_results,
        "holistic": holistic,
        "overall_verdict": holistic["overall_verdict"],
    }
