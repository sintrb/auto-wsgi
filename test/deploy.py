#!/usr/bin/env python

import os, sys, time, json, zipfile, requests, yaml

root = os.path.dirname(os.path.realpath(__file__))
zippath = root + '.zip'

config = yaml.load(open(os.path.join(root, 'deploy.yaml')))
upurl = config.get('upload')
if not config['appid']:
    raise Exception('need appid in deploy.yaml')


def _print(*args, **kwargs):
    sys.stdout.write(' '.join(args))
    end = kwargs.get('end', '\n')
    if end:
        sys.stdout.write(end)
    sys.stdout.flush()


def make_zip():
    _print('makezip', root, '->', zippath)
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
    _print('upload', zippath, '->', upurl)
    _print(requests.post(upurl, data={'config': json.dumps(config)}, files=files).text)


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
        'last': 0,
    }

    def on_progress(monitor):
        nproc = min(100, int(monitor.bytes_read * 100 / total) if total else 0)
        nlast = time.time()
        oproc = hodel['proc']
        olast = hodel['last']
        if (nproc - oproc) > 5 or (nlast - olast) > 1:
            proc = '%s%%' % nproc
            hodel['proc'] = nproc
            hodel['last'] = nlast
            barw = 50
            prow = int(barw * nproc / 100)
            _print('\ruploading... [%s%s] %s' % ('#' * prow, '-' * (barw - prow), proc), end='')

    e = MultipartEncoder(fields=data)
    m = MultipartEncoderMonitor(e, on_progress)
    _print('upload', zippath, '->', upurl)
    res = requests.post(upurl, data=m, headers={'Content-Type': m.content_type}).text
    _print()
    _print(res)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        upurl = sys.argv[1]
    if not upurl:
        _print('need upload server')
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
    # os.remove(zippath)
