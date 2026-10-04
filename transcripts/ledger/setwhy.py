import json,sys
def apply(updates, chart="author-axes"):
    L=json.load(open('ledger.json',encoding='utf-8'))
    sc=L["charts"][chart]["scores"]
    for (au,ax),why in updates.items():
        m=[x for x in sc if x["author"]==au and x["axis"]==ax]
        assert len(m)==1,(au,ax); m[0]["why"]=why
    json.dump(L,open('ledger.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
