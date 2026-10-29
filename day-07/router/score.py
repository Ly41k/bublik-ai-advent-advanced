import math
import statistics
from .core import LABELS, need

def wilson(k,n):
    z=1.96;p=k/n;d=1+z*z/n
    mid=(p+z*z/(2*n))/d
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [mid-half,mid+half]

def score(gold, predictions):
    need(len(gold)==60 and len(predictions)==60,'INCOMPLETE_60')
    need(len({g['sample_id'] for g in gold})==60,'GOLD_ID')
    need([g['sample_id'] for g in gold]==[p['sample_id'] for p in predictions], 'PREDICTION_IDS_OR_ORDER')
    need(all(g['label'] in LABELS and g['language'] in ('en','ru') for g in gold),'GOLD_LABEL')
    need(all(p.get('status')=='OK' and isinstance(p.get('raw'),str) and
             type(p.get('latency_seconds')) in (int,float) and
             math.isfinite(p['latency_seconds']) and p['latency_seconds']>=0 for p in predictions),'INFERENCE_INCOMPLETE')
    matrix=[[0]*7 for _ in LABELS]
    for g,p in zip(gold,predictions):
        matrix[LABELS.index(g['label'])][LABELS.index(p['raw']) if p['raw'] in LABELS else 6]+=1
    per=[]
    for i,label in enumerate(LABELS):
        tp=matrix[i][i];actual=sum(matrix[i]);pred=sum(r[i] for r in matrix)
        precision=tp/pred if pred else 0;recall=tp/actual if actual else 0
        per.append({'label':label,'n':actual,'precision':precision,'recall':recall,
                    'f1':2*precision*recall/(precision+recall) if precision+recall else 0})
    k=sum(matrix[i][i] for i in range(6));lat=sorted(p['latency_seconds'] for p in predictions)
    langs={}
    for lang in ('en','ru'):
        pairs=[(g,p) for g,p in zip(gold,predictions) if g['language']==lang]
        langs[lang]={'n':len(pairs),'correct':sum(g['label']==p['raw'] for g,p in pairs),
                     'format_valid':sum(p['raw'] in LABELS for g,p in pairs)}
    return {'n':60,'complete':True,'correct':k,'accuracy':k/60,
            'format_valid':60-sum(r[6] for r in matrix),'macro_f1':sum(r['f1'] for r in per)/6,
            'confusion':matrix,'gold_order':list(LABELS),'prediction_order':[*LABELS,'INVALID'],
            'per_class':per,'by_language':langs,'wilson_95':wilson(k,60),
            'zero_denominator_policy':'ZERO','latency_seconds':{'total':sum(lat),'median':statistics.median(lat),'p95_nearest_rank':lat[56]}}

def paired(gold,b,c):
    sb,sc=score(gold,b),score(gold,c)
    counts=dict.fromkeys(('improved','regressed','both_correct','both_wrong_same_raw','both_wrong_changed_raw'),0)
    for g,x,y in zip(gold,b,c):
        bx=x['raw']==g['label'];cy=y['raw']==g['label']
        k=('both_correct' if bx and cy else 'regressed' if bx else 'improved' if cy else
           'both_wrong_same_raw' if x['raw']==y['raw'] else 'both_wrong_changed_raw')
        counts[k]+=1
    n=counts['improved']+counts['regressed'];m=min(counts['improved'],counts['regressed'])
    p=min(1.,2*sum(math.comb(n,i) for i in range(m+1))/2**n) if n else 1.
    delta=sc['correct']-sb['correct']
    need(sum(counts.values())==60 and delta==counts['improved']-counts['regressed'],'PAIR_ALGEBRA')
    return {'paired_counts':counts,'delta_correct':delta,'delta_percentage_points':100*delta/60,
            'delta_macro_f1':sc['macro_f1']-sb['macro_f1'],'exact_mcnemar_two_sided_p':p,
            'result':'PROMPT_BASELINE_GAIN' if delta>0 else 'NO_PROMPT_BASELINE_GAIN',
            'caveat':'n=60; balanced artificial holdout, not natural prevalence; 1/60=1.667pp; no robust population gain claim'}

def summary(gold,a,b,c):
    return {'schema':'d7-safe-abc-v1','scope':'AGGREGATES_ONLY',
            'A':score(gold,a),'B':score(gold,b),'C':score(gold,c),'B_C':paired(gold,b,c)}
