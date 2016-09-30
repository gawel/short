# -*- coding: utf-8 -*-
import os
import base64
from operator import itemgetter
from webob import exc
from webob import Request
from webob import Response
from tinydb import TinyDB
from tinydb import Query

db_path = os.path.expanduser('~/.short.db')
db = TinyDB(db_path)

auth = os.environ.get('SHORT_AUTH')
if auth is not None:
    auth = base64.encodestring(auth)


def get_db(path):
    if len(path):
        db_name = path[0]
        if db_name == 'default':
            rdb = db
        else:
            rdb = db.table(db_name)
    else:
        db_name = 'default'
        rdb = db
    return db_name, rdb


def admin(req, resp):
    rauth = req.authorization
    if rauth != ('Basic', auth):
        return exc.HTTPForbidden()
    path = [p for p in req.path.split('/')[2:] if p]
    db_name, rdb = get_db(path)
    result = {}
    if req.method == 'POST':
        data = req.json
        for k in ('alias', 'url'):
            if k not in data:
                return exc.HTTPBadRequest()
        Q = Query()
        q = (Q.alias == data['alias']) | (Q.url == data['url'])
        res = rdb.search(q)
        if res:
            rdb.update(data, q)
        else:
            rdb.insert(data)
        result[db_name] = data
    elif req.method == 'GET':
        if rdb is db:
            for table in db.tables():
                result[table.strip('_')] = db.table(table).all()
        else:
            result[db_name] = rdb.all()
        bm = req.accept.best_match(['text/html', 'application/json'])
        if 'application/json' not in bm:
            body = '<html><body>'
            for k, v in sorted(result.items()):
                body += "<h2>{}</h2>".format(k)
                for item in sorted(v, key=itemgetter('alias')):
                    body += (
                        '<div><a href="{url}">{alias} - {url}</a><div>'
                    ).format(**item)
            body += '</body></html>'
            resp.content_type = 'text/html'
            resp.body = body
    if resp.content_type == 'application/json':
        resp.json = result
    return resp


def application(environ, start_response):
    req = Request(environ)
    resp = Response(content_type='application/json')
    if req.path_info.startswith('/admin/'):
        resp = admin(req, resp)
    else:
        path = [p for p in req.path.split('/') if p]
        if len(path) == 1:
            path.insert(0, '_default')
        db_name, alias = path[0:2]
        db_name, rdb = get_db([db_name])
        res = rdb.search(Query().alias == alias)
        if len(res):
            data = res[0]
            bm = req.accept.best_match(['text/html', 'application/json'])
            if 'application/json' in bm:
                resp.json = data
            else:
                resp = exc.HTTPFound(location=data['url'])
        else:
            resp = exc.HTTPNotFound()
    return resp(environ, start_response)
