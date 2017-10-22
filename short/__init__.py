# -*- coding: utf-8 -*-
import os
import base64
from operator import itemgetter
from webob import exc
from webob import Request
from webob import Response
from tinydb import TinyDB
from tinydb import Query

db_path = os.path.expanduser('~/.short.json')
db = TinyDB(db_path, sort_keys=True, indent=4)

auth = os.environ.get('SHORT_AUTH')
if auth is not None:
    auth = base64.encodestring(auth.encode('utf8')).strip().decode('utf8')


def get_db(path):
    if len(path):
        db_name = path[0]
        if db_name in ('d', 'default'):
            db_name = 'default'
            rdb = db.table('_default')
        else:
            rdb = db.table(db_name)
    else:
        db_name = 'default'
        rdb = db
    return db_name, rdb


def check_auth(req):
    rauth = req.authorization
    if rauth is None:
        resp = exc.HTTPUnauthorized()
        resp.www_authenticate = 'Basic realm="Auth"'
        return resp
    if rauth != ('Basic', auth):
        return exc.HTTPForbidden()


def clean(req, resp):
    for table in db.tables():
        items = db.table(table).all()
        if not len(items):
            db.purge_table(table)
    return resp


def admin(req, resp):
    err = check_auth(req)
    if err is not None:
        return err
    path = [p for p in req.path_info.strip('/').split('/', 3)[1:] if p]
    db_name, rdb = get_db(path)
    result = {}
    if req.method == 'DELETE':
        data = dict(alias=path[-1])
        rdb.remove(Query().alias == data['alias'])
        result = data
    elif req.method == 'POST':
        data = dict(alias=path[-1])
        try:
            data.update(req.json)
        except ValueError:
            return exc.HTTPBadRequest()
        for k in ('alias', 'url'):
            if k not in data:
                return exc.HTTPBadRequest()
        q = Query().alias == data['alias']
        res = rdb.search(q)
        if res:
            rdb.update(data, q)
        else:
            rdb.insert(data)
        result[db_name] = data
    elif req.method == 'GET':
        if rdb is db:
            for table in db.tables():
                items = db.table(table).all()
                result[table.strip('_')] = sorted(items,
                                                  key=itemgetter('alias'))
        else:
            result[db_name] = rdb.all()
        bm = req.accept.best_match(['text/html', 'application/json'])
        if 'application/json' not in bm:
            body = '<html><body>'
            for k, v in sorted(result.items()):
                body += "<h2>{}</h2>".format(k)
                body += "<ul>"
                for item in sorted(v, key=itemgetter('alias')):
                    body += (
                        '<li><a href="{url}">{alias:<10} - {url}</a></li>'
                    ).format(**item)
                body += "</ul>"
            body += '</body></html>'
            resp.content_type = 'text/html'
            resp.text = body
    if resp.content_type == 'application/json':
        resp.json = result
    return resp


def _application(environ, start_response):
    req = Request(environ)
    resp = Response()
    resp.content_type = 'application/json'
    resp.charset = 'utf8'
    if not req.path_info.strip('/').strip():
        resp = exc.HTTPNotFound()
    elif req.path_info.startswith('/admin/'):
        resp = admin(req, resp)
    elif req.path_info == "/clean":
        resp = clean(req, resp)
    else:
        bm = req.accept.best_match(['text/html', 'application/json'])
        path = [p for p in req.path_info.strip('/').split('/', 1) if p]
        if len(path) == 1:
            path.insert(0, '_default')
        db_name, alias = path[0:2]
        db_name, rdb = get_db([db_name])
        res = rdb.search(Query().alias == alias)
        if len(res):
            data = res[0]
            if 'application/json' in bm:
                resp.json = data
            else:
                resp = exc.HTTPFound(location=data['url'])
        else:
            resp = exc.HTTPNotFound()
    return resp


def application(environ, start_response):
    try:
        resp = _application(environ, start_response)
    except Exception as e:
        import traceback
        resp = Response()
        traceback.print_exc(file=resp.body_file)
    return resp(environ, start_response)
