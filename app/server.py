"""Local preview, execution and read-only replay API."""
import json
import re
import secrets
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from .runner import cases, preview, execute
from .run_records import ROOT, read_json


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, obj, kind='application/json; charset=utf-8'):
        raw = json.dumps(obj, ensure_ascii=False).encode() if kind.startswith('application/json') else obj
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def files(self):
        return list(self.server.runs_dir.rglob('*.json'))

    def do_GET(self):
        if self.path == '/':
            raw = (ROOT/'app/static/index.html').read_text(encoding='utf-8')
            return self.reply(200, raw.replace('__SESSION_TOKEN__', self.server.token).encode(), 'text/html; charset=utf-8')
        if self.path in ('/style.css', '/app.js'):
            suffix = 'text/css' if self.path.endswith('.css') else 'text/javascript'
            return self.reply(200, (ROOT/'app/static'/self.path[1:]).read_bytes(), suffix+'; charset=utf-8')
        if self.path.startswith('/api/') and self.headers.get('X-Assessment-Session') != self.server.token:
            return self.reply(403, {'error':'session_required'})
        if self.path == '/api/cases':
            return self.reply(200, dict(allow_paid=self.server.allow_paid,
                cases=[dict(id=c['id'], split=c['split'], question=c['question'], conditions=list(c['conditions'])) for c in cases()]))
        if self.path == '/api/runs':
            rows = []
            for p in self.files():
                r = read_json(p)
                if 'run_id' in r:
                    rows.append({k:r.get(k) for k in ('run_id','case_id','condition','variant','status','run_kind','utc')})
            return self.reply(200, sorted(rows, key=lambda r:r.get('utc') or '', reverse=True))
        if self.path.startswith('/api/runs/'):
            rid = self.path[len('/api/runs/'):]
            if not re.fullmatch(r'[A-Za-z0-9_-]+', rid):
                return self.reply(400, {'error':'invalid_run_id'})
            paths = [p for p in self.files() if p.stem == rid]
            if len(paths) == 1:
                return self.reply(200, read_json(paths[0]))
            return self.reply(404, {'error':'record_not_found'})
        return self.reply(404, {'error':'not_found'})

    def do_POST(self):
        if self.headers.get('X-Assessment-Session') != self.server.token:
            return self.reply(403, {'error':'session_required'})
        if self.path not in ('/api/preview','/api/run'):
            return self.reply(404, {'error':'not_found'})
        try:
            n = int(self.headers.get('Content-Length','0'))
            if not 0 < n <= 200000:
                raise ValueError('invalid_body_size')
            obj = json.loads(self.rfile.read(n))
            spec = {k:obj[k] for k in ('case_id','condition','variant')}
            pv = preview(spec['case_id'], spec['condition'], spec['variant'], self.server.config)
            if self.path == '/api/preview':
                return self.reply(200, pv)
            mode = obj.get('mode','dry')
            if mode not in ('dry','mock','paid'):
                raise ValueError('invalid_mode')
            if mode == 'paid' and not self.server.allow_paid:
                return self.reply(403, {'error':'paid_disabled'})
            fields = ('question','visible_passages','input_sha256','public_config_sha256')
            verified = all(k in obj for k in fields)
            if any(k in obj for k in fields) and (not verified or any(obj[k] != pv[k] for k in fields)):
                return self.reply(409, {'error':'input_changed_preview_again'})
            c = next(c for c in cases() if c['id'] == spec['case_id'])
            purpose = 'dev' if c['split'] == 'dev' else 'exploratory'
            result = execute(spec['case_id'], spec['condition'], spec['variant'], self.server.config,
                mock=mode=='mock', dry=mode=='dry', outdir=self.server.runs_dir/purpose,
                metadata={'purpose':purpose,'preview_verified':verified})
            self.reply(200, result)
        except (ValueError, KeyError, TypeError) as exc:
            self.reply(400, {'error':type(exc).__name__})
        except Exception as exc:
            self.reply(500, {'error':type(exc).__name__})

    def log_message(self, *args):
        pass


def make_server(config, port=8765, runs_dir=None, allow_paid=False):
    server = ThreadingHTTPServer(('127.0.0.1',port), Handler)
    server.config, server.token = config, secrets.token_urlsafe(24)
    server.runs_dir = Path(runs_dir) if runs_dir else ROOT/'runs'
    server.allow_paid = allow_paid
    return server


def serve(config, port=8765, allow_paid=False):
    server = make_server(config, port=port, allow_paid=allow_paid)
    print('http://127.0.0.1:'+str(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
