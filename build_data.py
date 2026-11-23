"""Regenerate the browser data after changing perfume_dataset.xlsx: python build_data.py"""
import ast, json, re
from pathlib import Path
import recommender as rc
root = Path(__file__).parent
p,c = rc.load_data(root/'perfume_dataset.xlsx')
X,f = rc.build_features(p)
labels,_,_ = rc.cluster_perfumes(X,f)
images = next(ast.literal_eval(n.value) for n in ast.parse((root/'app.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PERFUME_IMAGES' for t in n.targets))
rows = p.to_dict(orient='records')
for row, label in zip(rows,labels):
 key = re.sub(r'[^a-z0-9가-힣]','',str(row['향수명']).lower().replace('&','').replace('and',''))
 row['cluster'] = int(label)
 row['image'] = images.get(key) or next((v for k,v in images.items() if k in key or key in k),'')
(root/'data.js').write_text('window.PERFUME_DATA = '+json.dumps({'perfumes':rows,'colors':c.to_dict(orient='records')},ensure_ascii=False,allow_nan=False)+';\n')
print('Exported',len(rows),'perfumes and',len(c),'colors')
