def calculate_rule_score(base_part, candidate_part):
    score = 0
    reasons = []

    # Rule 1: Same category
    if base_part.category == candidate_part.category:
        score += 40
        reasons.append("Same category")

    # Rule 2: Same material
    if base_part.material and candidate_part.material:
        if base_part.material.lower() == candidate_part.material.lower():
            score += 30
            reasons.append("Same material")

    # Rule 3: Diameter within ±10%
    if base_part.diameter and candidate_part.diameter:
        diff = abs(base_part.diameter - candidate_part.diameter)
        if diff <= base_part.diameter * 0.10:
            score += 30
            reasons.append("Diameter within 10% range")

    return score, reasons
