from trust_swarm.report import build_markdown_report, build_json_report


def test_markdown_report_contains_all_sections(sample_trust_brief, sample_domain_result, sample_holistic_result):
    md = build_markdown_report(
        trust_brief=sample_trust_brief,
        domain_results=[sample_domain_result],
        holistic=sample_holistic_result,
    )
    assert "## Repo Overview" in md
    assert "## Domain Scorecards" in md
    assert "## Risk Detail" in md
    assert "## Compound Risks" in md
    assert "## Top Recommendations" in md
    assert "## Overall Verdict" in md


def test_markdown_report_includes_domain_score(sample_trust_brief, sample_domain_result, sample_holistic_result):
    md = build_markdown_report(
        trust_brief=sample_trust_brief,
        domain_results=[sample_domain_result],
        holistic=sample_holistic_result,
    )
    assert "Security" in md
    assert "AMBER" in md


def test_markdown_report_includes_overall_verdict(sample_trust_brief, sample_domain_result, sample_holistic_result):
    md = build_markdown_report(
        trust_brief=sample_trust_brief,
        domain_results=[sample_domain_result],
        holistic=sample_holistic_result,
    )
    assert "AMBER" in md


def test_json_report_has_expected_keys(sample_trust_brief, sample_domain_result, sample_holistic_result):
    report = build_json_report(
        trust_brief=sample_trust_brief,
        domain_results=[sample_domain_result],
        holistic=sample_holistic_result,
    )
    assert set(report.keys()) == {"trust_brief", "domain_results", "holistic", "overall_verdict"}


def test_json_report_overall_verdict_matches_holistic(sample_trust_brief, sample_domain_result, sample_holistic_result):
    report = build_json_report(
        trust_brief=sample_trust_brief,
        domain_results=[sample_domain_result],
        holistic=sample_holistic_result,
    )
    assert report["overall_verdict"] == "AMBER"
