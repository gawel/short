# -*- coding: utf-8 -*-
import os
import pytest
import short
import base64
from webtest import TestApp

db_path = '/tmp/short.db'


def rm():
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope='function')
def db(request):
    short.debug(mode=True)
    rm()
    db = short.db = short.TinyDB(db_path)
    db.insert(dict(alias='a', url='http://toto.com'))
    db.insert(dict(alias='b', url='http://toto.com'))
    a = db.table('a')
    a.insert(dict(alias='a', url='http://tata.com'))
    a.insert(dict(alias='b', url='http://tata.com'))
    request.addfinalizer(rm)
    return short.db


@pytest.fixture(scope='function')
def app(request):
    return TestApp(short.application)


@pytest.fixture(scope='function')
def admin_app(request):
    auth = base64.encodestring(b'admimin:passwd').strip().decode('utf8')
    return TestApp(short.application,
                   extra_environ={'HTTP_AUTHORIZATION': 'Basic ' + auth})
