# -*- coding: utf-8 -*-
import os
from operator import itemgetter
from webob import Request
from tinydb import (TinyDB, Query)
from bottle import (
    route, run, debug, request, response, default_app, redirect,
    auth_basic, abort, error,
)

db_path = os.path.expanduser('~/.short.json')
db = TinyDB(db_path, sort_keys=True, indent=4)

auth = tuple(os.environ.get('SHORT_AUTH', 'admimin:passwd').split(':'))

Alias = Query()


def check_auth(user, pw):
    if (user, pw) == auth:
        return True
    return False


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


@route('/clean')
def clean():
    for table in db.tables():
        items = db.table(table).all()
        if not len(items):
            db.purge_table(table)
    return redirect('/admin/')


@route('/admin/')
@route('/admin/<path:path>')
@auth_basic(check_auth)
def admin(path=''):
    req = Request(request.environ)
    path = path.strip('/')
    result = {}
    bm = req.accept.best_match(['text/html', 'application/json'])
    if not path:
        for table in db.tables():
            items = db.table(table).all()
            result[table.strip('_')] = sorted(items,
                                              key=itemgetter('alias'))
    else:
        db_name = '_default' if path == 'default' else path
        result[path] = db.table(db_name).all()
    print('bm', bm)
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
        response.content_type = 'text/html'
        return body
    return result


@route('/admin/', method='POST')
@route('/admin/<path:path>', method='POST')
@auth_basic(check_auth)
def admin_post(path=''):
    if request.content_type != 'application/json':
        abort(400)
    try:
        db_name, path = path.strip('/').split('/')
    except Exception:
        abort(400)
    if db_name in ('d', 'default', 'defaults'):
        db_name = '_default'
    rdb = db.table(db_name)
    data = {'alias': path}
    try:
        data.update(request.json)
    except ValueError:
        abort(400)
    for k in ('alias', 'url'):
        if k not in data:
            abort(400)
    q = Alias.alias == data['alias']
    res = rdb.search(q)
    if res:
        print('Update', rdb, data)
        rdb.update(data, q)
    else:
        print('Insert', rdb,  data)
        rdb.insert(data)
    db_name = db_name.strip('_')
    return {db_name: data}


@route('/admin/<path:path>', method='DELETE')
@auth_basic(check_auth)
def admin_delete(path='/'):
    path = path.strip('/')
    if '/' in path:
        try:
            db_name, path = path.split('/')
        except Exception:
            abort(400)
    else:
        db_name = '_default'
    if db_name not in db.tables():
        abort(404)
    rdb = db.table(db_name)
    data = dict(alias=path)
    rdb.remove(Alias.alias == data['alias'])
    return {}


@route('/<path:path>')
def index(path):
    req = Request(request.environ)
    bm = req.accept.best_match(['text/html', 'application/json'])
    print(path, bm)
    path = [p for p in path.split('/', 1) if p]
    if len(path) == 1:
        path.insert(0, '_default')
    db_name, alias = path[0:2]
    if db_name not in db.tables():
        abort(404)
    rdb = db.table(db_name)
    res = rdb.search(Alias.alias == alias)
    if len(res):
        data = res[0]
        if 'application/json' in bm:
            return data
        else:
            return redirect(data['url'])
    else:
        abort(404)


@error(404)
def error_404(e):
    req = Request(request.environ)
    bm = req.accept.best_match(['text/html', 'application/json'])
    if 'application/json' in bm:
        return {}
    return "404"


def main():
    if 'ADMIN_PASSWORD' not in os.environ:
        debug(mode=True)
    run(host='0.0.0.0', port=4444, reloader=True)


application = default_app()
