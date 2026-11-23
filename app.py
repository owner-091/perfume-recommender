"""퍼스널 향수 추천 앱 (Streamlit)
실행:  streamlit run app.py

사용법
 1) 마음에 드는 색을 누르거나, 내 사진(옷·소품 등)을 올립니다.
 2) 어울리는 향수가 이미지·브랜드·이름과 함께 나타납니다.
 3) 향수의 '자세히 보기'를 누르면 향조·노트·달콤함·시원함·분위기를 볼 수 있어요.

향수 이미지 우선순위:
 1) images/ 폴더 내 향수 ID 파일 (예: images/1.jpg)
 2) 코드 내 PERFUME_IMAGES 매핑 URL (브랜드/향수명 자동 매칭)
 3) 기본 병 일러스트 (SVG)
"""
import base64
import glob
import os
import re

import pandas as pd
import streamlit as st
from PIL import Image

import recommender as rc

st.set_page_config(page_title="나만의 퍼스널 향수", page_icon="🌸", layout="wide")

PERFUME_IMAGES = {
    "no5edp": "https://www.chanel.com/puls-img/1792742321177-vl-holiday-2026-packshot-p1-n5-edp-dotcom-mp-mob_3200x3000.jpg",
    "no5": "https://www.chanel.com/puls-img/1792742321177-vl-holiday-2026-packshot-p1-n5-edp-dotcom-mp-mob_3200x3000.jpg",
    "cocomademoiselle": "https://static.lottedfs.com/prod/prd-img/55/59/06/00/00/01/10000065955_7.jpg/dims/resize/590x590",
    "blackopium": "https://www.yslbeautyus.com/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-ysl-master-catalog/default/dw5afbe332/Black%20Opium%20Packshots/BO%20EDP/3365440787919.jpg",
    "blackorchid": "https://sdcdn.io/tf/tf_sku_T00401_2000x2000_0.png",
    "replicajazzclub": "https://www.sephora.com/productimages/sku/s1602259-main-zoom.jpg",
    "jazzclub": "https://www.sephora.com/productimages/sku/s1602259-main-zoom.jpg",
    "bleudechanel": "https://www.chanel.com/images/t_one/w_0.51,h_0.51,c_crop/q_auto:good,f_auto,fl_lossy,dpr_1.1/w_1240/bleu-de-chanel-eau-de-parfum-spray-3-4fl-oz--packshot-default-107360-9564894232606.jpg",
    "baccaratrouge540": "https://static.lottedfs.com/prod/prd-img/48/70/96/00/00/02/20000967048_10.jpg/dims/resize/590x590",
    "siedp": "https://www.giorgioarmanibeauty-usa.com/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-gab-master-catalog/default/dwe431d531/products/A218/A218%202025%20packshots/3605521816658_01.png",
    "si": "https://www.giorgioarmanibeauty-usa.com/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-gab-master-catalog/default/dwe431d531/products/A218/A218%202025%20packshots/3605521816658_01.png",
    "chloeedp": "https://www.chloe.com/dw/image/v2/BLMX_PRD/on/demandware.static/-/Sites-chloe-master/default/dwfc6ec9dc/images/all-images/CHCA64980409/5PkOQ09jQN6w6uYNBP9kHA_50c613c9.jpeg?sw=1440&sfrm=png&q=90",
    "chloe": "https://www.chloe.com/dw/image/v2/BLMX_PRD/on/demandware.static/-/Sites-chloe-master/default/dwfc6ec9dc/images/all-images/CHCA64980409/5PkOQ09jQN6w6uYNBP9kHA_50c613c9.jpeg?sw=1440&sfrm=png&q=90",
    "lavieestbelle": "https://www.lancome-usa.com/on/demandware.static/-/Sites-lancome-us-Library/default/dw8391a246/images/pdp/compare-lveb-edp.jpg",
    "daisy": "https://media.ulta.com/i/ulta/2151611?w=800&h=800&fmt=auto",
    "missdiorbloomingbouquet": "https://www.dior.com/dw/image/v2/BGXS_PRD/on/demandware.static/-/Sites-master_dior/default/dw73279557/Y0996612/Y0996612_C099700102_E01_ZHC.jpg?sw=1800",
    "peonyblushsuede": "https://static.lottedfs.com/prod/prd-img/97/21/07/02/00/01/10002072197_4.jpg/dims/resize/590x590",
    "flowerbomb": "https://us.viktor-rolf.com/on/demandware.static/-/Sites-vr-master-catalog/default/dwfd1b8cbe/flowerbomb/vr_frag_2025_Flowerbomb_PRETTY_PEONY_PDP_eD2C_BTF_desktop_about_fragrance.jpg",
    "jadore": "https://whitelabel.dior.com/dw/image/v2/BJSW_PRD/on/demandware.static/-/Sites-dior_id-Library/en_ID/dw0279638e/JDR_S2-24_Mood_Lambris_1850x2000.jpg?sw=768&sfrm=jpg",
    "her": "https://assets.burberry.com/is/image/Burberryltd/170DBE43-9B00-40B1-A766-F1482E6F263D?$BBY_V3_SL_1$&wid=1501&hei=1500",
    "englishpearfreesia": "https://www.jomalone.co.za/media/export/cms/66913/PDP_Assets/PDP_Module_EPF_1_Mobile.jpg",
    "woodsageseasalt": "https://sdcdn.io/jm/jm_sku_L41501_3000x3000_0S.png",
    "terredhermes": "https://assets.hermes.com/is/image/hermesproduct/107188V0_front_wm_102?$product_default_bg$",
    "tamdao": "https://noseparis.com/media/opti_image/webp/catalog/product/cache/2a6b0744b87cbe1990f7a65c1fd3659e/t/a/tam-dao-edp_2.webp",
    "blanche": "https://image-cdn.hypb.st/https%3A%2F%2Fbae.hypebeast.com%2Ffiles%2F2021%2F06%2Fbyredo-blanche-collectors-edition-perfume-bottle-campaign-notes-release-0.jpg?w=960&cbr=1&q=90&fit=max",
    "mojaveghost": "https://shoprescuespa.com/cdn/shop/files/shop-rescue-spa-mojave-ghost-eau-de-parfum-bottle-a1b2c3.jpg?v=1781038787&width=1200",
    "santal33": "https://n.nordstrommedia.com/it/7be3d6c4-450f-485b-bb25-e3b95260f342.jpeg",
    "another13": "https://n.nordstrommedia.com/it/c2adc6bf-a678-4de4-84be-c34d65a3f4de.jpeg",
    "orpheon": "https://noseparis.com/media/opti_image/webp/catalog/product/cache/2a6b0744b87cbe1990f7a65c1fd3659e/p/a/packshot-orphe_on_edt_2-diptyque_1.webp",
    "lazysundaymorning": "https://www.maisonmargiela-fragrances.eu/on/demandware.static/-/Sites-margiela-master-catalog/default/dw91700225/images/products/MM133/LSM_EDT.jpg",
    "bythefireplace": "https://www.maisonmargiela-fragrances.us/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-maisonmargiela-us-Library/default/dwe5819be2/videos/MM_THUMBNAIL_BTF.webp?sw=700&sh=700&sm=cut&sfrm=jpg&q=70",
}

BRAND_FALLBACK_IMAGES = {
    "byredo": PERFUME_IMAGES["mojaveghost"],
    "lelabo": PERFUME_IMAGES["another13"],
    "diptyque": PERFUME_IMAGES["orpheon"],
    "maisonmargiela": PERFUME_IMAGES["bythefireplace"],
    "jomalone": PERFUME_IMAGES["woodsageseasalt"],
}


def normalize_key(text):
    s = str(text).lower().replace("&", "").replace("and", "")
    return re.sub(r"[^a-z0-9가-힣]", "", s)


@st.cache_data
def prepare(k=5):
    perfumes, colors = rc.load_data()
    X, feats = rc.build_features(perfumes)
    labels, _, names = rc.cluster_perfumes(X, feats, k=k)
    return perfumes, colors, labels, names


perfumes, colors, labels, cluster_names = prepare()
style_color = colors.groupby("스타일")["HEX 코드"].apply(list).to_dict()
SCORE_BG = {"시크/모던": "#E8E8EE", "러블리/플로럴": "#FDE8EF", "내추럴/우디": "#E6F2E6"}


def text_on(hexcode):
    r, g, b = (int(hexcode[i:i + 2], 16) for i in (1, 3, 5))
    return "#fff" if 0.299 * r + 0.587 * g + 0.114 * b < 150 else "#000"


def bottle_svg(hexcode):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 150">
<rect width="120" height="150" rx="12" fill="#faf7f5"/>
<rect x="46" y="14" width="28" height="22" rx="4" fill="#3a3a3a"/>
<rect x="52" y="36" width="16" height="10" fill="#bdbdbd"/>
<rect x="26" y="46" width="68" height="90" rx="14" fill="#fff" stroke="#bbb" stroke-width="2"/>
<rect x="30" y="76" width="60" height="56" rx="10" fill="{hexcode}"/>
<rect x="36" y="54" width="8" height="70" rx="4" fill="#fff" opacity=".45"/>
</svg>'''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def render_img_tag(src):
    st.markdown(
        f'<div style="width:100%;aspect-ratio:1/1;overflow:hidden;border-radius:12px;'
        f'background:#fff;display:flex;align-items:center;justify-content:center;">'
        f'<img src="{src}" style="width:100%;height:100%;object-fit:contain;">'
        f'</div>',
        unsafe_allow_html=True,
    )


def show_image(row):
    found = glob.glob(os.path.join("images", f"{row['ID']}.*"))
    if found:
        st.image(found[0], use_container_width=True)
        return

    name_key = normalize_key(row["향수명"])
    brand_key = normalize_key(row["브랜드"])

    img_url = PERFUME_IMAGES.get(name_key)
    if not img_url:
        for k, url in PERFUME_IMAGES.items():
            if k in name_key or name_key in k:
                img_url = url
                break

    if not img_url:
        img_url = BRAND_FALLBACK_IMAGES.get(brand_key)

    if img_url:
        render_img_tag(img_url)
    else:
        hexes = style_color[row["스타일"]]
        st.markdown(
            f'<img src="{bottle_svg(hexes[int(row["ID"]) % len(hexes)])}" style="width:100%;border-radius:12px">',
            unsafe_allow_html=True,
        )


def stretch_button(label, **kw):
    try:
        return st.button(label, width="stretch", **kw)
    except TypeError:
        return st.button(label, use_container_width=True, **kw)


def chip(text, bg="#eee", fg="#000"):
    return (f"<span style='background:{bg};color:{fg};padding:4px 12px;border-radius:14px;"
            f"font-size:13px;margin-right:6px;display:inline-block;margin-bottom:4px'>{text}</span>")


@st.dialog("향수 정보")
def show_detail(perfume_id):
    r = perfumes[perfumes["ID"] == perfume_id].iloc[0]
    c1, c2 = st.columns([1, 2])
    with c1:
        show_image(r)
    with c2:
        st.markdown(f"### {r['향수명']}")
        st.caption(r["브랜드"])
        st.markdown(chip(r["스타일"], SCORE_BG[r["스타일"]]), unsafe_allow_html=True)
    st.markdown(f"**향조 계열**  {r['향조 계열']}")
    st.markdown(f"**탑노트**  {r['탑노트']}")
    st.markdown(f"**미들노트**  {r['미들노트']}")
    st.markdown(f"**베이스노트**  {r['베이스노트']}")
    st.markdown(f"🍯 **달콤함**  {r[rc.SWEET]} / 5")
    st.progress(int(r[rc.SWEET]) / 5)
    st.markdown(f"❄️ **시원함**  {r[rc.FRESH]} / 5")
    st.progress(int(r[rc.FRESH]) / 5)
    st.markdown("**분위기 키워드**")
    st.markdown("".join(chip(k.strip(), "#f1ecf7") for k in r["분위기 키워드"].split(",")),
                unsafe_allow_html=True)
    same = perfumes[(labels == labels[perfumes.index[perfumes["ID"] == perfume_id][0]])
                    & (perfumes["ID"] != perfume_id)]
    if len(same):
        st.markdown("**비슷한 향의 향수** (같은 향 군집)")
        st.write(", ".join(f"{b} {n}" for b, n in zip(same["브랜드"], same["향수명"])))


st.title("🌸 나만의 퍼스널 향수 찾기")
st.caption("색을 누르거나 내 사진을 올리면, 어울리는 향수를 찾아드려요.")

if "picked" not in st.session_state:
    st.session_state.picked = []


def toggle(name):
    p = st.session_state.picked
    p.remove(name) if name in p else p.append(name)


tab1, tab2 = st.tabs(["🎨 색으로 찾기", "📷 사진으로 찾기"])

with tab1:
    st.write("끌리는 색을 눌러보세요. (여러 개 선택 가능, 다시 누르면 해제)")
    for style, group in colors.groupby("스타일", sort=False):
        st.markdown(f"**{style}**")
        cols = st.columns(len(group))
        for col, (_, c) in zip(cols, group.iterrows()):
            with col:
                st.markdown(f"<div style='background:{c['HEX 코드']};height:44px;border-radius:10px;"
                            f"border:1px solid #ddd'></div>", unsafe_allow_html=True)
                stretch_button(c["색상명"], key=f"c_{c['색상명']}", on_click=toggle, args=(c["색상명"],),
                               type="primary" if c["색상명"] in st.session_state.picked else "secondary")
    if st.session_state.picked:
        st.button("선택 모두 해제", on_click=lambda: st.session_state.picked.clear())

with tab2:
    photo = st.file_uploader("내 사진을 올려주세요 (옷, 소품, 방 분위기 등)", type=["jpg", "jpeg", "png", "webp"])
    st.caption("사진의 대표 색을 분석해서 가장 가까운 색으로 연결해요. 흰 배경은 자동으로 제외합니다.")

votes = {}
name_to_style = dict(zip(colors["색상명"], colors["스타일"]))
for n in st.session_state.picked:
    votes[name_to_style[n]] = votes.get(name_to_style[n], 0) + 1

photo_info = []
if photo is not None:
    photo_info = rc.photo_palette(Image.open(photo), colors)
    for p in photo_info:
        votes[p["스타일"]] = votes.get(p["스타일"], 0) + p["비율"] * 2

st.divider()
if not votes:
    st.info("색을 하나 이상 누르거나 사진을 올리면 향수가 나타나요.")
    st.stop()

probs = rc.votes_to_probs(votes)
best = max(probs, key=probs.get)

if photo_info:
    st.markdown("**사진에서 찾은 대표 색**")
    st.markdown("".join(
        chip(f"{p['색상명']} {p['비율'] * 100:.0f}%", p["HEX 코드"], text_on(p["HEX 코드"])) for p in photo_info),
        unsafe_allow_html=True)
st.subheader(f"나의 이미지는 '{best}'에 가장 가까워요")
st.bar_chart(pd.Series(probs, name="확률"), height=160)

with st.expander("🍯❄️ 취향 더 맞추기 (선택)"):
    use_pref = st.checkbox("달콤함/시원함 취향도 반영", value=False)
    c1, c2 = st.columns(2)
    sweet = c1.slider("달콤함", 1, 5, 3, disabled=not use_pref)
    fresh = c2.slider("시원함", 1, 5, 3, disabled=not use_pref)
    count = st.slider("보여줄 향수 개수", 3, len(perfumes), 6)

ranked = rc.rank_all(perfumes, labels, probs, sweet if use_pref else None, fresh if use_pref else None)
top = ranked.head(count)

st.subheader("어울리는 향수")
st.caption("'자세히 보기'를 누르면 향조·노트·분위기를 볼 수 있어요.")
per_row = 3
rows = [top.iloc[i:i + per_row] for i in range(0, len(top), per_row)]
for chunk in rows:
    cols = st.columns(per_row)
    for col, (_, r) in zip(cols, chunk.iterrows()):
        with col, st.container(border=True):
            show_image(r)
            st.markdown(f"**{r['향수명']}**")
            st.caption(f"{r['브랜드']} · 일치도 {r['일치도(%)']}%")
            if stretch_button("자세히 보기", key=f"p_{r['ID']}"):
                show_detail(int(r["ID"]))
