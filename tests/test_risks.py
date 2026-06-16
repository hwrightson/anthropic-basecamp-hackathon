from trust_swarm.risks import RISKS, DOMAIN_GROUPS, RISK_BY_ID


def test_all_22_risks_present():
    assert len(RISKS) == 22


def test_every_risk_has_required_fields():
    required = {"id", "name", "domain", "principle", "sub_dimension", "root_causes", "evaluation_options"}
    for risk in RISKS:
        assert required <= risk.keys(), f"Risk {risk.get('id')} missing fields"


def test_domain_groups_cover_all_risks():
    all_in_groups = {rid for ids in DOMAIN_GROUPS.values() for rid in ids}
    all_risk_ids = {r["id"] for r in RISKS}
    assert all_in_groups == all_risk_ids


def test_domain_groups_has_five_domains():
    assert set(DOMAIN_GROUPS.keys()) == {
        "security", "reliability", "transparency_fairness", "accountability", "human_factors"
    }


def test_risk_by_id_lookup():
    risk = RISK_BY_ID["system_instability"]
    assert risk["domain"] == "reliability"
