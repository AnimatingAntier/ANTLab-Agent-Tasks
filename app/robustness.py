"""No-model equivalence check. Write the prediction before invoking the rules."""
import copy
import datetime
import random
from pathlib import Path
from .runner import get_case
from .student import improve, prepare_messages
from .run_records import write_json, digest, exclusive_lock


def check_case(cid,kind,seed,outdir):
    case=get_case(cid)
    if case is None or kind not in ('ids','order','both'):
        raise ValueError('invalid_case_or_variant')
    by_id={p['id']:p for p in case['passages']}
    original=[copy.deepcopy(by_id[i]) for i in case['conditions']['R0']]
    changed=copy.deepcopy(original)
    mapping={}
    if kind in ('ids','both'):
        for index,p in enumerate(changed):
            mapping[p['id']]='X'+str(index+1)
            p['id']=mapping[p['id']]
            p['source']='等价来源/'+str(index+1)
    if kind in ('order','both'):
        random.Random(seed).shuffle(changed)
    out=Path(outdir)
    out.mkdir(parents=True,exist_ok=True)
    with exclusive_lock(out/'.variant.lock'):
        if (out/'prediction.json').exists():
            raise ValueError('variant_already_exists_use_new_directory')
        prediction=dict(case_id=cid,kind=kind,seed=seed,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            prediction='若主体记录可唯一辨识，重映射ID和打乱输入顺序后应得到相同正文顺序及相同前两段关联；若锚点不唯一则保留输入，顺序可以变化。',
            limitation='仅检验组织及输入组件，不检验模型回答稳定性。',
            original=original,transformed=changed,id_mapping=mapping)
        write_json(out/'prediction.json',prediction)
        first=improve(case['question'],copy.deepcopy(original))
        second=improve(case['question'],copy.deepcopy(changed))
        a,b=[p['text'] for p in first],[p['text'] for p in second]
        result=dict(case_id=cid,run_kind='local_rule',call_count=0,
            prediction_sha256=digest(prediction),same_text_set=sorted(a)==sorted(b),
            same_content_order=a==b,same_linked_prefix=a[:2]==b[:2],
            original_selected=first,transformed_selected=second,
            original_messages=prepare_messages(case['question'],first),
            transformed_messages=prepare_messages(case['question'],second))
        write_json(out/'result.json',result)
        return result
