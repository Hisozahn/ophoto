#!/usr/bin/env python3

import aiopg
import bcrypt
import markdown
import os.path
import psycopg2
import re
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
import unicodedata
import json

from users_db import Database

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("db_host", default="127.0.0.1", help="user database host")
define("db_port", default=27017, help="user database port")
define("db_database", default="users", help="user database name")

SECURE_COOKIE_NAME="ophoto_user"

class Application(tornado.web.Application):
    def __init__(self, db):
        self.db = db
        handlers = [
            (r"/", HomeHandler),
            (r"/auth/create", AuthCreateHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/secret", SecretHandler),
        ]
        settings = dict(
            xsrf_cookies=False,
            cookie_secret="JIPe32fieoHF(Eb32o98fe]32[e3[2u*(FQhue2dsqnjodehiw&*Te2yvdbiew",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie(SECURE_COOKIE_NAME)

class HomeHandler(BaseHandler):
    async def get(self):
        self.write( {"code": 1000, "message": "OK"})


class AuthCreateHandler(BaseHandler):
    async def post(self):
        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(self.get_argument("password")),
            bcrypt.gensalt(),
        )
        try:
            user_id = await self.application.db.create_user(
                self.get_argument("user"),
                tornado.escape.to_unicode(hashed_password),
            )
        except Exception as err:
            self.write( {"code": 999, "message": err})
        self.set_secure_cookie(SECURE_COOKIE_NAME, str(user_id))
        self.write( {"code": 1000, "message": "Authenticated"})


class AuthLoginHandler(BaseHandler):
    async def post(self):
        user = await self.application.db.get_user(self.get_argument("user"))
        if user is None:
            self.write( {"code": 999, "message": "User is not found" })
            return
        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(self.get_argument("password")),
            tornado.escape.utf8(user.hashed_password),
        )
        hashed_password = tornado.escape.to_unicode(hashed_password)
        if hashed_password == user.hashed_password:
            self.set_secure_cookie(SECURE_COOKIE_NAME, str(user._id))
            self.write( {"code": 1000, "message": "Authenticated"})
        else:
            self.write( {"code": 999, "message": "Invalid user/password pair"})


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(SECURE_COOKIE_NAME)
        self.write( {"code": 1000, "message": "OK"})

class SecretHandler(BaseHandler):
    async def get(self):
        if not self.current_user:
            self.write({"code": 999, "message": "No secret for you"})
            return
        self.write({"code": 1000, "message": "Secret is secret"})


async def main():
    tornado.options.parse_command_line()

    db = Database(options.db_host, options.db_port, options.db_database)
    app = Application(db)
    app.listen(options.port)
    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)

'''
class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        id = self.get_argument("id", None)
        entry = None
        if id:
            entry = await self.queryone("SELECT * FROM entries WHERE id = %s", int(id))
        self.render("compose.html", entry=entry)

    @tornado.web.authenticated
    async def post(self):
        id = self.get_argument("id", None)
        title = self.get_argument("title")
        text = self.get_argument("markdown")
        html = markdown.markdown(text)
        if id:
            try:
                entry = await self.queryone(
                    "SELECT * FROM entries WHERE id = %s", int(id)
                )
            except NoResultError:
                raise tornado.web.HTTPError(404)
            slug = entry.slug
            await self.execute(
                "UPDATE entries SET title = %s, markdown = %s, html = %s "
                "WHERE id = %s",
                title,
                text,
                html,
                int(id),
            )
        else:
            slug = unicodedata.normalize("NFKD", title)
            slug = re.sub(r"[^\w]+", " ", slug)
            slug = "-".join(slug.lower().strip().split())
            slug = slug.encode("ascii", "ignore").decode("ascii")
            if not slug:
                slug = "entry"
            while True:
                e = await self.query("SELECT * FROM entries WHERE slug = %s", slug)
                if not e:
                    break
                slug += "-2"
            await self.execute(
                "INSERT INTO entries (author_id,title,slug,markdown,html,published,updated)"
                "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
                self.current_user.id,
                title,
                slug,
                text,
                html,
            )
        self.redirect("/entry/" + slug)
'''
