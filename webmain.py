#!/usr/bin/env python


import os, json, zipfile, shutil
import tornado.web
from autowsgi import AW

gaw = AW()


class BasehHandler(tornado.web.RequestHandler):
    aw = gaw

    def return_json(self, data):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(data))
        self.flush()


class HelloHandler(BasehHandler):
    def get(self):
        self.write("Hello, world")


class AppListHandler(BasehHandler):
    def get(self):
        self.return_json(self.aw.get_applist())


class UploadApplicationHandler(BasehHandler):
    def error(self, msg):
        self.write(msg)

    def post(self, *args, **kwargs):
        config = json.loads(self.get_body_argument('config'))
        if not config or not config.get('appid'):
            return self.error('no config')
        appid = config.pop('appid')
        metas = self.request.files["file"]
        if not metas:
            return self.error('no file')
        meta = metas[0]
        name = meta['filename']
        if not name.endswith('.zip'):
            return self.error('not a zip file')

        data = meta['body']
        apppath = os.path.join(self.aw.apps_path, '%s.zip' % appid)
        with open(apppath, 'wb') as up:
            up.write(data)
        expath = os.path.join(self.aw.apps_path, appid)
        if os.path.exists(expath):
            shutil.rmtree(expath)
        f = zipfile.ZipFile(apppath, 'r')
        for file in f.namelist():
            f.extract(file, expath)
        config['path'] = expath
        config.setdefault('host', '%s.iwebsite.inruan.com' % appid)
        self.aw.add_application(appid, **config)
        self.aw.run_application(appid)
        print('add', appid)
        self.write('deploy %s success!  http://%s' % (appid, config['host']))


tornado_app = tornado.web.Application([
    (r"/upload", UploadApplicationHandler),
    (r"/apps", AppListHandler),
    (r"/", HelloHandler),
])


def echook():
    print('started!')


def main():
    from tornado.options import options, define
    define('port', type=int, default=8080)
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port, address='0.0.0.0')
    tornado.ioloop.IOLoop.instance().add_callback(echook)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
