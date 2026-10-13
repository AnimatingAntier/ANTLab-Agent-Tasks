"""One entry point for local work and explicitly requested API calls."""
import argparse
import json
import os
from pathlib import Path
from .run_records import ROOT, write_json


def load_credentials(path):
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        key,sep,value=line.strip().partition('=')
        if sep and key.strip()=='DEEPSEEK_API_KEY':
            value=value.strip()
            if len(value)>=2 and value[0]==value[-1] and value[0] in ('"',"'"):
                value=value[1:-1]
            if not value:
                raise ValueError('empty_deepseek_key')
            os.environ['ASSESSMENT_API_KEY']=value
            return
    raise ValueError('deepseek_key_not_found')


def main():
    parser=argparse.ArgumentParser(description='基础题：预览、运行、冻结、审计、离线评分')
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run')
    run.add_argument('--case',required=True)
    run.add_argument('--condition',default='R0')
    run.add_argument('--variant',choices=['baseline','improved'],default='baseline')
    run.add_argument('--outdir')
    mode=run.add_mutually_exclusive_group()
    mode.add_argument('--paid',action='store_true')
    mode.add_argument('--mock',action='store_true')
    mode.add_argument('--dry-run',action='store_true')
    serve=sub.add_parser('serve')
    serve.add_argument('--port',type=int,default=8765)
    serve.add_argument('--allow-paid',action='store_true')
    freeze=sub.add_parser('freeze')
    freeze.add_argument('--output',required=True)
    freeze.add_argument('--max-calls',type=int,default=48)
    freeze.add_argument('--experiment-id',default='basic-main-v1')
    batch=sub.add_parser('batch')
    batch.add_argument('--manifest',required=True)
    batch.add_argument('--runs')
    mode=batch.add_mutually_exclusive_group()
    mode.add_argument('--paid',action='store_true')
    mode.add_argument('--dry-run',action='store_true')
    batch.add_argument('--resume',action='store_true')
    batch.add_argument('--retry-of')
    for command in (run,serve,freeze,batch):
        command.add_argument('--config',default=str(ROOT/'config/example.json'))
        command.add_argument('--env-file')
    audit=sub.add_parser('audit')
    audit.add_argument('--manifest',required=True)
    audit.add_argument('--runs',required=True)
    audit.add_argument('--output',default=str(ROOT/'results/basic-audit.json'))
    score=sub.add_parser('score')
    score.add_argument('--runs',required=True)
    score.add_argument('--manifest',required=True)
    score.add_argument('--labels',default=str(ROOT/'results/scoring/labels.json'))
    score.add_argument('--reviews',default=str(ROOT/'results/scoring/reviews.jsonl'))
    score.add_argument('--output-dir',default=str(ROOT/'results'))
    variant=sub.add_parser('robustness')
    variant.add_argument('--case',required=True)
    variant.add_argument('--kind',choices=['ids','order','both'],default='both')
    variant.add_argument('--seed',type=int,default=20261006)
    variant.add_argument('--outdir',required=True)
    sub.add_parser('status')
    args=parser.parse_args()
    try:
        if getattr(args,'env_file',None):
            load_credentials(args.env_file)
        if args.command=='run':
            from .runner import execute,load_config
            destination=Path(args.outdir) if args.outdir else None
            if args.paid and destination and not destination.resolve().is_relative_to((ROOT/'runs').resolve()):
                raise ValueError('paid_runs_must_stay_inside_project_runs')
            result=execute(args.case,args.condition,args.variant,load_config(args.config),
                dry=not args.paid and not args.mock,mock=args.mock,outdir=destination)
            result={k:result.get(k) for k in ('run_id','status','api_status','http_status','format_status','call_count')}
        elif args.command=='serve':
            from .server import serve
            from .runner import load_config
            serve(load_config(args.config),args.port,args.allow_paid)
            return
        elif args.command=='freeze':
            from .experiment import freeze_manifest
            m=freeze_manifest(args.config,args.output,args.max_calls,args.experiment_id)
            result=dict(experiment_id=m['experiment_id'],jobs=len(m['jobs']),output=args.output)
        elif args.command=='batch':
            from .experiment import run_batch
            from .run_records import read_json
            m=read_json(args.manifest)
            dest=Path(args.runs) if args.runs else ROOT/'runs/main'/m['experiment_id']
            if args.paid and not dest.resolve().is_relative_to((ROOT/'runs').resolve()):
                raise ValueError('paid_runs_must_stay_inside_project_runs')
            result=run_batch(args.manifest,args.config,dest,paid=args.paid,dry=not args.paid,
                resume=args.resume,retry_of=args.retry_of)
        elif args.command=='audit':
            from .experiment import audit_manifest
            result=audit_manifest(args.manifest,args.runs);write_json(args.output,result)
        elif args.command=='score':
            from .scoring import score_directory
            result=score_directory(args.runs,args.manifest,args.labels,args.reviews,args.output_dir)
        elif args.command=='robustness':
            from .robustness import check_case
            r=check_case(args.case,args.kind,args.seed,args.outdir)
            result={k:r[k] for k in ('case_id','call_count','same_text_set','same_content_order','same_linked_prefix')}
        else:
            from .budget import consumed
            result=dict(consumed_calls=consumed(ROOT/'runs'),authorized_limit=64)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as exc:
        parser.exit(2,'操作未完成：'+(str(exc) if isinstance(exc,ValueError) else type(exc).__name__)+'\n')
