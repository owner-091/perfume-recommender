"""퍼스널 향수 추천 알고리즘 모듈 (recommender.py)"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

SWEET = "달콤함"
FRESH = "시원함"


def load_data(path="perfume_dataset.xlsx"):
    """엑셀 파일에서 향수 데이터와 색상 기준 데이터를 로드합니다."""
    perfumes = pd.read_excel(path, sheet_name="향수 데이터")
    colors = pd.read_excel(path, sheet_name="색상 데이터")
    return perfumes, colors


def build_features(perfumes):
    """향수 데이터로부터 군집화용 특성 행렬(X)을 구축합니다."""
    # 범주형(스타일, 향조 계열) + 수치형(달콤함, 시원함) 결합
    cat_cols = ["스타일", "향조 계열"]
    num_cols = [SWEET, FRESH]

    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X_cat = encoder.fit_transform(perfumes[cat_cols].fillna(""))

    scaler = MinMaxScaler()
    X_num = scaler.fit_transform(perfumes[num_cols].fillna(3))

    X = np.hstack([X_cat, X_num])
    feats = list(encoder.get_feature_names_out(cat_cols)) + num_cols
    return X, feats


def cluster_perfumes(X, feats, k=5):
    """K-평균(K-Means) 알고리즘으로 유사한 향수 군집을 분류합니다."""
    n_clusters = min(k, len(X))
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    names = {i: f"향 군집 {i + 1}" for i in range(n_clusters)}
    return labels, km, names


def _hex_to_rgb(hexcode):
    h = str(hexcode).lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def photo_palette(img, colors, top_n=4):
    """업로드된 이미지에서 흰 배경을 제외한 주요 색상을 추출하여 기준 색상과 매핑합니다."""
    img_small = img.convert("RGB").resize((80, 80))
    pixels = np.array(img_small).reshape(-1, 3).astype(float)

    # 흰 배경(R, G, B 모두 235 이상) 자동 제외
    non_white = pixels[~np.all(pixels >= 235, axis=1)]
    if len(non_white) == 0:
        non_white = pixels

    ref_rgbs = np.array([_hex_to_rgb(h) for h in colors["HEX 코드"]])
    # 각 픽셀과 가장 가까운 기준 색상 인덱스 계산 (유클리드 거리)
    dists = np.linalg.norm(non_white[:, None, :] - ref_rgbs[None, :, :], axis=2)
    nearest = np.argmin(dists, axis=1)

    counts = np.bincount(nearest, minlength=len(colors))
    total = counts.sum()
    if total == 0:
        return []

    top_idx = np.argsort(counts)[::-1][:top_n]
    results = []
    for idx in top_idx:
        if counts[idx] == 0:
            continue
        row = colors.iloc[idx]
        results.append({
            "색상명": row["색상명"],
            "HEX 코드": row["HEX 코드"],
            "스타일": row["스타일"],
            "비율": float(counts[idx] / total),
        })
    return results


def votes_to_probs(votes):
    """스타일별 가중치 점수를 확률 분포로 변환합니다."""
    total = sum(votes.values())
    if total <= 0:
        return {k: 1.0 / len(votes) for k in votes}
    return {k: v / total for k, v in votes.items()}


def rank_all(perfumes, labels, probs, sweet=None, fresh=None):
    """사용자 스타일 확률 및 달콤함/시원함 취향을 반영하여 향수 일치도(%) 순위를 산출합니다."""
    df = perfumes.copy()
    style_scores = df["스타일"].map(lambda s: probs.get(s, 0.0)).values

    if sweet is not None and fresh is not None:
        # 1~5 스케일을 0~1로 정규화 후 유클리드 거리 계산
        d_sweet = (df[SWEET].values - sweet) / 4.0
        d_fresh = (df[FRESH].values - fresh) / 4.0
        dist = np.sqrt((d_sweet ** 2 + d_fresh ** 2) / 2.0)
        pref_sim = np.clip(1.0 - dist, 0.0, 1.0)
        final_score = 0.65 * style_scores + 0.35 * pref_sim
    else:
        final_score = style_scores

    # 직관적인 일치도(%) 스케일링 (최대 확률 대비 정규화 및 가독성 보정)
    max_prob = max(probs.values()) if probs else 1.0
    if sweet is None:
        norm_score = np.clip(final_score / max(max_prob, 1e-6), 0.0, 1.0)
        match_pct = np.round(55 + norm_score * 43).astype(int)
    else:
        match_pct = np.round(50 + np.clip(final_score, 0.0, 1.0) * 48).astype(int)

    df["일치도(%)"] = match_pct
    df = df.sort_values(by=["일치도(%)", "ID"], ascending=[False, True]).reset_index(drop=True)
    return df
