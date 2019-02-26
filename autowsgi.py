#!/usr/bin/env python


import os, json, time, shutil

print(os.path.dirname(__file__))
class AW(object):
    base_path = os.path.dirname(__file__)
    data = {
        'apps': {}
    }

    def __init__(self):
        self.load()

    @property
    def data_path(self):
        return os.path.join(self.base_path, 'data.json')

    def load(self):
        try:
            self.data = json.load(open(self.data_path))
        except:
            import traceback
            traceback.print_exc()

    def save(self):
        with open(self.data_path, 'w') as f:
            json.dump(self.data, f)

    def _wrap_path(self, sub):
        path = os.path.join(self.base_path, sub)
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    @property
    def nginx_path(self):
        return self._wrap_path('nginx')

    @property
    def temp_path(self):
        return self._wrap_path('temp')

    @property
    def apps_path(self):
        return self._wrap_path('apps')

    def refresh_script(self):
        temp_path = self.temp_path
        nginx_path = self.nginx_path
        if len(os.listdir(nginx_path)):
            shutil.rmtree(nginx_path)
            nginx_path = self.nginx_path
        for appid, config in self.data['apps'].items():
            # shell
            param = {
                'appid': appid,
                'temp': temp_path,
            }
            param.update(config)
            param.setdefault('gunparam', '')
            param.setdefault('host', '%s.demo.inruan.com' % appid)
            shell = '''
kill -9 `cat "{temp}/{appid}.pid"` > /dev/null 2>&1
rm "{temp}/{appid}.pid" 2>&1
cd "{path}"
gunicorn {gunparam} -D -p {temp}/{appid}.pid {wsgi} -b unix:{temp}/{appid}.socket
            '''.format(**param)
            with open(os.path.join(temp_path, '%s_start.sh' % appid), 'w') as f:
                f.write(shell)

            # nginx
            nginx = '''
upstream iwebm_{appid}_server {{
    server unix:{temp}/{appid}.socket fail_timeout=0;
}}

server {{
    listen 80;
    server_name {host};
    gzip on;
    gzip_http_version 1.0;
    gzip_min_length 1024;
    gzip_comp_level 3;
    gzip_types text/plain application/json text/json;
    client_max_body_size 20M;
    
    location / {{
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_read_timeout 300s;
        if (!-f $request_filename) {{
            proxy_pass http://iwebm_{appid}_server;
            break;
        }}
    }}
    location ~ ^/(static)/ {{
       root {path}/;
    }}
    location ~ ^(/upload/.*)\.(\S+) {{
        root {path}/;
        if ($arg_force){{
            # force handle image
            proxy_pass http://iwebm_{appid}_server;
            add_header  "Image-Handle" "force handle image";
            break;
        }}
        # try with files
        try_files $1-$arg_type.$2 @handleimg;
        add_header  "Image-Handle" "try with files";
    }}
    location @handleimg {{
        # handle image with server
        proxy_set_header Host $http_host;
        proxy_pass http://iwebm_{appid}_server;
        add_header  "Image-Handle" "handle image with server";
        break;
    }}
}}            
            '''.format(**param)
            with open(os.path.join(nginx_path, '%s.conf' % appid), 'w') as f:
                f.write(nginx)

    def add_application(self, appid, **kwargs):
        self.data['apps'][appid] = kwargs
        self.save()
        self.refresh_script()

    def run_application(self, appid):
        self.run_shell(os.path.join(self.temp_path, '%s_start.sh' % appid))
        self.run_nginx('reload')

    def sudo(self, cmd):
        try:
            # pwd = open(os.path.join(self.base_path, 'password')).read().strip()
            # r = os.system('echo "%s" | sudo -S %s' % (pwd, cmd))
            r = os.system('sudo -S %s' % (cmd))
            return r
        except Exception as e:
            import traceback
            traceback.print_exc()
        return None

    def run_nginx(self, sig):
        r = self.sudo('nginx -s %s' % sig)
        if r != 0:
            raise Exception('执行nginx错误%s' % (r or ''))

    def run_shell(self, path):
        import subprocess
        ov = os.environ.get('DJANGO_SETTINGS_MODULE')
        if ov:
            del os.environ['DJANGO_SETTINGS_MODULE']
        r = subprocess.call(['bash', path], close_fds=True)
        if ov:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', ov)
        if r != 0:
            raise Exception(u'%s执行脚本失败:%s' % (path, r))

# aw = AW()
# aw.add_application('local', path='/Users/robin/DO/GitHub/auto-wsgi', wsgi='test:tornado_app', gunparam='-k tornado', t=2)
# aw.add_application('local', path='/Users/robin/DO/Py/iticket', wsgi='iticket.wsgi:application')
# aw.run_application('local')
# while True:
#     time.sleep(10)
