# -*- coding: utf-8 -*-
from chut import ini
from chut import console_script
import requests


@console_script
def main(args):
    """Usage: short [--serve] [-l] [-d] [<alias>] [<url>]"""
    if args['--serve']:
        import waitress
        from short import application
        waitress.serve(application)
        return
    cfg = ini('~/.short.ini').short
    url = cfg.url.strip('/')
    admin_url = url + '/admin/'
    auth = tuple(cfg.auth.split(':'))
    session = requests.Session()
    session.headers.update({'Accept': 'application/json'})
    session.auth = auth
    if args['-l']:
        resp = session.get(admin_url)
        for db_name, items in resp.json().items():
            if len(items):
                print(db_name)
                print('=' * len(db_name))
                for item in items:
                    print('{alias:<10}{url}'.format(**item))
                print('')
        return
    alias = args['<alias>']
    url = args['<url>']
    if alias:
        if args['-d']:
            resp = session.delete(url + alias)
        elif url:
            resp = session.post(admin_url,
                                json=dict(alias=alias, url=url))
        print(resp)
