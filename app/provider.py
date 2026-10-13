"""Adapted from the public starter. No automatic retries or hidden calls."""
import json
import math
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


def validate_config(config, require_key=False):
    if not isinstance(config, dict) or set(config) - {'provider', 'endpoint', 'model', 'parameters', 'timeout_seconds'}:
        raise ValueError('invalid_config_fields')
    if any(not isinstance(config.get(k), str) or not config[k] for k in ('provider', 'endpoint', 'model')):
        raise ValueError('missing_config_fields')
    url = urlparse(config['endpoint'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('endpoint_requires_https')
    params = config.get('parameters', {})
    if not isinstance(params, dict) or set(params) & {'messages', 'model', 'stream'}:
        raise ValueError('reserved_generation_parameters')
    timeout = config.get('timeout_seconds', 90)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('invalid_timeout')
    if require_key:
        if not os.environ.get('ASSESSMENT_API_KEY'):
            raise ValueError('missing_api_key')
        if 'YOUR_' in config['endpoint'] or not config['model'].isascii() or 'å¡«å†™' in config['model']:
            raise ValueError('placeholder_config')


def call_model(messages, config, mock=False):
    base = dict(response=None, response_raw=None, usage=None, usage_source='unavailable',
                elapsed_seconds=None, http_status=None, call_count=0)
    if mock:
        base.update(status='mock', response={'choices': [{'message': {
            'content': '{"answer":"MOCK_NOT_EVIDENCE","citations":[]}'}}]})
        return base
    try:
        validate_config(config, require_key=True)
        body = {'model': config['model'], 'messages': messages, 'stream': False, **config.get('parameters', {})}
        req = urllib.request.Request(config['endpoint'],
            data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode(),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.environ['ASSESSMENT_API_KEY']})
    except (ValueError, TypeError, KeyError) as exc:
        base.update(status='config_error', error_code=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        return base
    start = time.perf_counter()
    base['call_count'] = 1
    try:
        with urllib.request.urlopen(req, timeout=config.get('timeout_seconds', 90)) as reply:
            raw = reply.read().decode('utf-8')
            base.update(response_raw=raw, http_status=reply.status)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            base.update(status='invalid_provider_json')
        else:
            base.update(status='ok', response=parsed, usage=parsed.get('usage') if isinstance(parsed, dict) else None)
            if base['usage'] is not None:
                base['usage_source'] = 'api'
    except urllib.error.HTTPError as exc:
        base.update(status='http_error', http_status=exc.code, error_code='HTTP_' + str(exc.code))
        exc.close()
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeError) as exc:
        base.update(status='transport_error', error_code=type(exc).__name__)
    finally:
        base['elapsed_seconds'] = time.perf_counter() - start
    return base
