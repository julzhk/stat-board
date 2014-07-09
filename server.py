import tornado.ioloop
import tornado.web

from tornado.options import define, options, parse_command_line

define("port", default=8080, help="run on the given port", type=int)

clients = []

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("templates/index.html")


app = tornado.web.Application([
    (r'/', IndexHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()