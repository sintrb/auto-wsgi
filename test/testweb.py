#!/usr/bin/env python


import tornado.web


class HelloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


tornado_app = tornado.web.Application([
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
