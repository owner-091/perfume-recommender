# 나만의 퍼스널 향수 찾기

GitHub Pages에서 실행되는 향수 추천 앱입니다. `index.html`, `style.css`, `web-app.js`, `data.js`만으로 동작하며 별도 서버나 Streamlit 로그인이 필요 없습니다.

- 색상 다중 선택, 사진 대표색 분석, 달콤함/시원함 취향 반영, 추천 개수 조정, 향수 상세 정보
- 사진은 브라우저 안에서 분석하며 외부로 전송하지 않습니다.
- 원본 엑셀의 향수 20종과 색상 12종을 사용합니다.
- 추천 점수 공식은 원본 `recommender.py`와 동일하며 실제 선호 확률이 아닙니다.
- KMeans 군집은 원본 코드로 미리 계산해 `data.js`에 포함합니다.
- 제품 이미지가 로드되지 않으면 향수병 일러스트로 대체합니다.
- 사진은 80×80으로 축소하고 흰 배경을 제외합니다. 브라우저와 Pillow의 리샘플링 차이로 사진 색상 비율은 약간 다를 수 있습니다.

## 배포
GitHub Settings → Pages → Deploy from a branch → `main` / `(root)`.

## 데이터 수정
`perfume_dataset.xlsx` 수정 후 `pip install -r requirements.txt` 및 `python build_data.py`를 실행해 `data.js`를 다시 생성하고 커밋하세요.

원본 Python/Streamlit 코드도 보존했습니다. 로컬에서 실행하려면 `streamlit run app.py`를 사용하세요.
