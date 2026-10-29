"""Future local Mac runtime. Heavy imports ONLY inside admitted operations."""
import importlib.metadata as md
import math
import os
import platform
import sys
import time
from pathlib import Path
from .core import *

STACK={'mlx':'0.32.4','mlx-lm':'0.32.2','transformers':'5.21.0','huggingface_hub':'1.33.0'}
TRAIN={'fine_tune_type':'lora','num_layers':8,'lora_parameters':{
        'rank':8,'scale':20.0,'dropout':0.0,'keys':['self_attn.q_proj','self_attn.v_proj']},
       'batch_size':4,'iters':150,'learning_rate':0.0001,'optimizer':'adam',
       'max_seq_length':512,'mask_prompt':True,'seed':20261029,
       'steps_per_report':10,'steps_per_eval':50,'val_batches':-1,'steps_per_save':150,
       'grad_checkpoint':False,'grad_accumulation_steps':1,'clear_cache_threshold':0}
DECODE={'max_new_tokens':12,'temperature':0.0,'sampler':'greedy','seed':20261029,
        'context_limit':2048,'cleanup':False,'skip_special_tokens':False,'request_cache':'NEW_EACH_ITEM'}

def environment():
    need(sys.platform=='darwin' and platform.machine()=='arm64','BLOCKED_MAC_RUNTIME_NOT_AVAILABLE')
    need(sys.version_info[:3]==(3,13,3),'BLOCKED_PYTHON_VERSION')
    need(ud.unidata_version=='15.1.0','BLOCKED_UNICODE_VERSION')
    need(all(md.version(k)==v for k,v in STACK.items()),'BLOCKED_DEPENDENCIES')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',
                      WANDB_MODE='disabled',SWANLAB_MODE='disabled',TOKENIZERS_PARALLELISM='false')

def model_inventory(model_path):
    p=Path(model_path)
    need(p.is_absolute() and p.is_dir() and p.name==REVISION,'BLOCKED_MODEL_NOT_AVAILABLE')
    required={'config.json','tokenizer_config.json','tokenizer.json'}
    names={f.name for f in p.iterdir() if f.is_file()}
    need(required<=names and any(n.endswith('.safetensors') for n in names),'BLOCKED_MODEL_NOT_AVAILABLE')
    need(not any(n.endswith('.py') for n in names),'BLOCKED_REMOTE_CODE')
    cfg=read_json(p/'config.json')
    need(not cfg.get('quantization') and not cfg.get('quantization_config') and not cfg.get('auto_map'),'BLOCKED_MODEL_CONFIG')
    need(cfg.get('model_type')=='llama' and cfg.get('hidden_size')==960 and cfg.get('num_hidden_layers')==32,'BLOCKED_MODEL_IDENTITY')
    allowed={n for n in names if n.endswith(('.json','.safetensors','.jinja')) or n=='tokenizer.model'}
    return {n:sha((p/n).read_bytes()) for n in sorted(allowed)}

def token_checks(tok,rows,prompt):
    need(tok.model_max_length>=512,'TOKENIZER_CONTEXT')
    maxlen=0
    for r in rows:
        prefix=tok.apply_chat_template(chat(r,prompt)['messages'][:-1],add_generation_prompt=True,return_dict=False)
        full=tok.apply_chat_template(chat(r,prompt)['messages'],return_dict=False)
        label=tok.encode(r['label'],add_special_tokens=False)
        suffix=full[len(prefix):]
        need(full[:len(prefix)]==prefix and suffix[:len(label)]==label,'MASK_PREFIX_OR_LABEL')
        need(len(suffix)>len(label) and suffix[len(label)] in tok.eos_token_ids,'MASK_LABEL_EOS')
        need(tok.decode(suffix[len(label)+1:],skip_special_tokens=False,clean_up_tokenization_spaces=False) in ('','\n'),'TEMPLATE_TAIL')
        need(len(full)<=TRAIN['max_seq_length'] and len(prefix)+DECODE['max_new_tokens']<=2048,'OVERLONG_STOP_NO_TRUNCATION')
        maxlen=max(maxlen,len(full))
    return {'n':len(rows),'max_full_tokens':maxlen,'mask_prefix_label_eos':'VERIFIED_LOCAL_TOKENIZER_ONLY'}

def prepare(model_path,rows,prompt):
    environment();inventory=model_inventory(model_path)
    from mlx_lm.utils import load_tokenizer
    config=read_json(Path(model_path)/'config.json')
    tok=load_tokenizer(Path(model_path),{'local_files_only':True,'trust_remote_code':False},eos_token_ids=config.get('eos_token_id'))
    checks=token_checks(tok,rows,prompt)
    need(min(config['max_position_embeddings'],tok.model_max_length)>=DECODE['context_limit'],'CONTEXT_LIMIT')
    return tok,{'model_id':MODEL,'revision':REVISION,'files':inventory,
                'stack':STACK,'python':'3.13.3','unicode':'15.1.0','train':TRAIN,'decode':DECODE,
                'template_sha256':sha(tok.chat_template.encode()),'eos_token_ids':sorted(tok.eos_token_ids),
                'token_checks':checks,'prompt_sha256':sha(prompt.encode())}

def prompts(tok,rows,prompt,arm):
    result=[]
    for r in rows:
        messages=[{'role':'user','content':r['text']}]
        if arm!='A':messages.insert(0,{'role':'system','content':prompt})
        tokens=tok.apply_chat_template(messages,add_generation_prompt=True,return_dict=False)
        need(len(tokens)+DECODE['max_new_tokens']<=2048,'EVAL_OVERLONG_STOP')
        result.append(tokens)
    return result

def evaluate(model_path,rows,prompt,arm,adapter=None,prediction_path=None):
    need(arm in ('A','B','C') and (adapter is not None)==(arm=='C'),'ARM_ADAPTER')
    from mlx_lm import load
    from mlx_lm.generate import generate_step
    from mlx_lm.sample_utils import make_sampler
    import mlx.core as mx
    start=time.perf_counter()
    model,tok=load(str(model_path),adapter_path=str(adapter) if adapter else None,
                   tokenizer_config={'local_files_only':True,'trust_remote_code':False},trust_remote_code=False)
    mx.synchronize();load_seconds=time.perf_counter()-start
    # This is a fresh base instance per arm; no adapter in A/B and no request KV reuse.
    tokenized=prompts(tok,rows,prompt,arm)
    if prediction_path is not None:save_new(prediction_path,[],jsonl=True)
    out=[]
    for r,tokens in zip(rows,tokenized):
        mx.random.seed(DECODE['seed']);mx.synchronize();start=time.perf_counter();generated=[];stop='LENGTH';terminal=None
        for t,_ in generate_step(mx.array(tokens),model,max_tokens=DECODE['max_new_tokens'],sampler=make_sampler(0.0),prompt_cache=None):
            if t in tok.eos_token_ids:stop='EOS';terminal=t;break
            generated.append(t)
        mx.synchronize();elapsed=time.perf_counter()-start
        raw=tok.decode(generated,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        out.append({'sample_id':r['sample_id'],'raw':raw,'token_ids':generated,'stop_reason':stop,'terminal_eos_id':terminal,
                    'status':'OK','latency_seconds':elapsed,'prompt_tokens':len(tokens),
                    'rendered_prompt_token_ids':tokens})
        if prediction_path is not None:
            with Path(prediction_path).open('ab') as f:f.write(encoded(out[-1])+b'\n')
    del model
    mx.clear_cache()
    return out,{'model_load_seconds':load_seconds,'latency_scope':'tokenized_ready_to_device_synchronized_end',
                'prompt_tokens':sum(len(t) for t in tokenized),'generated_tokens':sum(len(p['token_ids']) for p in out),
                'stop_counts':dict(Counter(p['stop_reason'] for p in out)),
                'A_template_generic_system_present':('<|im_start|>system' in tok.decode(tokenized[0],skip_special_tokens=False)) if arm=='A' else False}

def train_once(model_path,rows,prompt,adapter_dir,tokenizer):
    from mlx_lm import load
    from mlx_lm.tuner.datasets import ChatDataset,CacheDataset
    from mlx_lm.tuner.trainer import train,TrainingArgs,iterate_batches
    from mlx_lm.tuner.utils import linear_to_lora_layers
    import mlx.core as mx
    import mlx.optimizers as optim
    from mlx.utils import tree_flatten
    from functools import partial
    adapter_dir=Path(adapter_dir)
    adapter_dir.mkdir(mode=0o700)  # no resume, existing directory fails
    save_new(adapter_dir/'adapter_config.json',TRAIN)
    start=time.perf_counter();mx.random.seed(TRAIN['seed'])
    model,tok=load(str(model_path),tokenizer_config={'local_files_only':True,'trust_remote_code':False},trust_remote_code=False)
    model.freeze();need(len(model.layers)==32,'MODEL_LAYERS')
    linear_to_lora_layers(model,8,TRAIN['lora_parameters'],use_dora=False)
    weights=dict(tree_flatten(model.trainable_parameters()))
    expected={f'model.layers.{i}.self_attn.{proj}.{part}' for i in range(24,32)
              for proj in ('q_proj','v_proj') for part in ('lora_a','lora_b')}
    need(set(weights)==expected,'TRAINABLE_LORA_ONLY')
    train_rows=[chat(r,prompt) for r in rows if r['split']=='train']
    valid_rows=[chat(r,prompt) for r in rows if r['split']=='valid']
    tr=ChatDataset(train_rows,tokenizer,mask_prompt=True);va=ChatDataset(valid_rows,tokenizer,mask_prompt=True)
    # Test actual installed ChatDataset offsets, not an assumed independent renderer.
    for dataset in (tr,va):
        for item in dataset._data:
            tokens,offset=dataset.process(item)
            prefix=tokenizer.apply_chat_template(item['messages'][:-1],add_generation_prompt=True,return_dict=False)
            need(tokens[:offset]==prefix and offset==len(prefix) and len(tokens)<=512,'LOADER_MASK_OR_TRUNCATION')
    class Losses:
        def __init__(self):self.train=[];self.valid=[]
        def append(self,name,info):
            safe={k:info[k] for k in ('iteration',name+'_loss')}
            need(math.isfinite(float(safe[name+'_loss'])),'NONFINITE_LOSS')
            getattr(self,'valid' if name=='val' else 'train').append(safe)
            # Private diagnostic evidence survives a later failed/incomplete training.
            with (adapter_dir/'losses.private.jsonl').open('ab') as f:f.write(encoded(safe)+b'\n')
        def on_train_loss_report(self,x):self.append('train',x)
        def on_val_loss_report(self,x):self.append('val',x)
    cb=Losses()
    args=TrainingArgs(**{k:TRAIN[k] for k in ('batch_size','iters','val_batches','steps_per_report',
        'steps_per_eval','steps_per_save','max_seq_length','grad_checkpoint','grad_accumulation_steps','clear_cache_threshold')},
        adapter_file=str(adapter_dir/'adapters.safetensors'))
    train(model,optim.Adam(learning_rate=TRAIN['learning_rate']),CacheDataset(tr),CacheDataset(va),args=args,
          iterate_batches=partial(iterate_batches,seed=TRAIN['seed']),training_callback=cb)
    need(cb.train and cb.train[-1]['iteration']==150 and len(cb.train)==15 and len(cb.valid)==4,'TRAIN_NOT_COMPLETE')
    weights=dict(tree_flatten(model.trainable_parameters()))
    saved=mx.load(str(adapter_dir/'adapters.safetensors'))
    need(set(saved)==expected and all(bool(mx.all(mx.isfinite(x)).item()) for x in saved.values()),'ADAPTER_CONTENT')
    need(all(bool(mx.array_equal(saved[k],weights[k]).item()) for k in expected),'ADAPTER_SAVE_MISMATCH')
    del weights,model
    reloaded,_=load(str(model_path),adapter_path=str(adapter_dir),
                    tokenizer_config={'local_files_only':True,'trust_remote_code':False},trust_remote_code=False)
    params=dict(tree_flatten(reloaded.parameters()))
    need(all(k in params and bool(mx.array_equal(params[k],saved[k]).item()) for k in expected),'ADAPTER_RELOAD_MISMATCH')
    del params,reloaded;mx.clear_cache()
    return {'status':'TRAIN_COMPLETE','iterations':150,'passes':3,'batch_size':4,'validation_rows':40,
            'selection':'FINAL_PLANNED_STEP_NO_EVAL_SELECTION','adapter_reload':'TENSOR_IDENTICAL',
            'runtime_seconds':time.perf_counter()-start,'losses':{'train':cb.train,'valid':cb.valid},
            'adapter_sha256':sha((adapter_dir/'adapters.safetensors').read_bytes()),
            'adapter_config_sha256':sha((adapter_dir/'adapter_config.json').read_bytes())}
