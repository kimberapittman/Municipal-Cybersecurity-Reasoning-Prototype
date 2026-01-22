# logic/reasoning.py

from typing import List, Dict

def apply_crosswalk(selected_csf_ids: List[str], crosswalk: List[Dict]):
    """
    Given CSF outcome IDs selected by the user,
    return the PFCE principles and rationale mapped to them.
    """

    results = []
    for csf_id in selected_csf_ids:
        match = next((item for item in crosswalk if item["csf_id"] == csf_id), None)
        if match:
            results.append({
                "csf_id": csf_id,
                "csf_outcome": match["csf_outcome"],
                "pfce": match["pfce"],
                "rationale": match["rationale"]
            })
    return results


def summarize_pfce(principles: List[str]):
    """
    Provide a user-friendly summary of PFCE principles involved.
    """
    if not principles:
        return "No ethical principles triggered."

    unique_principles = sorted(set(principles))
    return ", ".join(unique_principles)


def analyze_open_ended_description(description: str):
    """
    Placeholder for free-text analysis.
    Later, this may allow keyword detection,
    prompting the user for refined CSF categories.
    """

    if not description:
        return []

    # Example stub you can expand later
    return ["This description suggests possible mission impact or data exposure."]
