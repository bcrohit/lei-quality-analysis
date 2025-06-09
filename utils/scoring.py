import pandas as pd
def calculate_quality_score(df):
    weights = {
        "Completeness": 40,
        "CountryValid": 15,
        "DateConsistent": 15,
        "UniqueLEI": 15,
        "NotExpired": 15,
    }
    
    score = pd.Series(0, index=df.index)
    for check, weight in weights.items():
        score += df[check].astype(int) * weight
    
    df["QualityScore"] = score
    df["QualityLabel"] = pd.cut(
        df["QualityScore"],
        bins=[-1, 60, 80, 100],
        labels=["Poor", "Moderate", "Good"]
    )
    
    return df