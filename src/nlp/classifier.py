"""
Zero-shot classifier stub.
Returns hard-coded buckets until real impl. added.
"""
def split_four_pillars(items):
    # TODO: real zero-shot classifier
    buckets = {"terrorism": [], "organised": [], "financial": [], "cyber": []}
    for it in items:
        buckets["cyber"].append(it)   # dump everything into one bucket for now
    return buckets
