def rugpull_score(liquidity, holders, volume):

    score = 0

    if liquidity < 50000:
        score += 40

    if holders < 200:
        score += 30

    if volume < 10000:
        score += 30

    return min(score, 100)