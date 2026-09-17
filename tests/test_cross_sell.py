import pandas as pd


def test_association_rules_matching_with_real_casing():
    """Old code lowercased+underscored product names — never matched rule antecedents."""
    rules = pd.DataFrame({
        "antecedents": [
            frozenset({"Personal Loan", "Credit Card"}),
            frozenset({"Student Loan"}),
            frozenset({"Fixed Deposits"}),
        ],
        "consequents": [
            frozenset({"Savings Account"}),
            frozenset({"Credit Card"}),
            frozenset({"Insurance"}),
        ],
        "confidence": [0.7, 0.6, 0.5],
        "lift": [1.5, 1.2, 1.1],
    })

    seg_products = ["Personal Loan", "Travel Credit Card", "Mutual Funds"]

    # OLD (broken) approach — lowercased+underscored never matches original casing
    old_prod_set = {p.lower().replace(" ", "_") for p in seg_products}
    old_mask = rules["antecedents"].apply(lambda x: bool(set(x) & old_prod_set))
    assert old_mask.sum() == 0, "Old approach should match nothing (documents the bug)"

    # NEW (fixed) approach — compare with original casing
    new_prod_set = set(seg_products)
    new_mask = rules["antecedents"].apply(lambda x: bool(set(x) & new_prod_set))
    assert new_mask.sum() == 1, "Should match the 'Personal Loan' rule"
    assert "Personal Loan" in list(rules[new_mask]["antecedents"].iloc[0])
