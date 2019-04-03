#!/usr/bin/env python

import os, json, zipfile, requests, yaml

root = os.path.dirname(os.path.realpath(__file__))
zippath = root + '.zip'
# zippath = '/tmp/t.zip'

config = yaml.load(open(os.path.join(root, 'deploy.yaml')))
upurl = config.get('upload')
if not config['appid']:
    raise Exception('need appid in deploy.yaml')


def make_zip():
    print('makezip', root, '->', zippath)
    if os.path.exists(zippath):
        os.remove(zippath)
    z = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(root):
        fpath = dirpath.replace(root, '')
        for filename in filenames:
            if '.svn' in filename or '.git' in filename or '.idea' in filename:
                continue
            z.write(os.path.join(dirpath, filename), os.path.join(fpath, filename))
    z.close()


def upload_zip():
    global upurl
    files = {
        'file': open(zippath, 'rb')
    }
    print('upload', zippath, '->', upurl)
    print(requests.post(upurl, data={'config': json.dumps(config)}, files=files).text)


def upload_zip_with_progress():
    from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
    global upurl
    data = {
        'config': json.dumps(config),
        'file': (os.path.basename(zippath), open(zippath, 'rb'), 'application/zip')
    }
    total = os.path.getsize(zippath)
    hodel = {
        'proc': 0,
    }

    def on_progress(monitor):
        nproc = int(monitor.bytes_read * 100 / total) if total else 0
        oproc = hodel['proc']
        if (nproc - oproc) > 5:
            proc = '%s%%' % min(nproc, 100)
            hodel['proc'] = nproc
            print('\rupload', proc)

    e = MultipartEncoder(fields=data)
    m = MultipartEncoderMonitor(e, on_progress)
    print('upload', zippath, '->', upurl)
    print(requests.post(upurl, data=m, headers={'Content-Type': m.content_type}).text)


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        upurl = sys.argv[1]
    if not upurl:
        print('need upload server')
        exit(0)
    make_zip()
    has_requests_toolbelt = False
    try:
        import requests_toolbelt

        has_requests_toolbelt = True
    except:
        pass
    if has_requests_toolbelt:
        upload_zip_with_progress()
    else:
        upload_zip()
