# -*- coding: utf-8 -*-


def test_secure_admin(app):
    resp = app.get('/admin/', status='*')
    assert resp.status_int == 401


def test_admin(admin_app, db):
    resp = admin_app.get('/admin/', headers={'Accept': 'application/json'})
    assert resp.status_int == 200
    data = resp.json
    assert len(data['default']) == 2
    assert len(data['a']) == 2

    resp = admin_app.get('/admin/a/', headers={'Accept': 'application/json'})
    assert resp.status_int == 200
    data = resp.json
    assert 'default' not in data
    assert len(data['a']) == 2

    resp = admin_app.post_json('/admin/a/',
                               dict(url='http://tata.com'),
                               status='*')
    assert resp.status_int == 400

    data = dict(alias='c', url='http://tata.com')
    resp = admin_app.post_json('/admin/a/', data)
    assert resp.json['a'] == data

    data.pop('alias')
    resp = admin_app.post_json('/admin/a/c/', data)
    assert resp.json['a'] == dict(data, alias='c')

    resp = admin_app.get('/a/c')
    assert resp.status_int == 302

    resp = admin_app.delete('/admin/a/c')
    assert resp.status_int == 200
    assert resp.json == {}


def test_app(app, db):
    resp = app.get('/a')
    assert resp.status_int == 302
    assert resp.location == 'http://toto.com'

    resp = app.get('/a', headers={"Accept": "application/json"})
    assert resp.status_int == 200
    assert 'alias' in resp.json
    assert 'url' in resp.json

    resp = app.get('/a/b')
    assert resp.status_int == 302
    assert resp.location == 'http://tata.com'
