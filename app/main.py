
import orl_settings

import sys
import os
import mongoengine
from tornado import web, ioloop

config = orl_settings.ORLSettings()
settings = {
        'debug': config.debug,
        'cookie_secret': config.cookie_secret,
        'template_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
        'static_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
}

application = web.Application([
    (r'/', 'home.HomeHandler'),
    (r'/login', 'login.LoginHandler'),
    (r'/logout', 'login.LogoutHandler'),
    (r'/register', 'login.RegisterHandler'),
    (r'/dashboard', 'dashboard.DashboardHandler'),
    (r'/add', 'runs.AddRunHandler'),
], **settings)

application.config = config



if __name__ == '__main__':
    port = 11000
    if len(sys.argv) > 1:
        port = sys.argv[1]

    mongoengine.connect(
            application.config.db_name, 
            host=application.config.db_host, 
            port=application.config.db_port, 
            username=application.config.db_username, 
            password=application.config.db_password)

    application.listen(port)
    ioloop.IOLoop.instance().start()

