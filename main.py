import os
import re
import json
import pytz
import psutil
import subprocess
import tornado.ioloop
import tornado.web
from datetime import datetime

EST = pytz.timezone('US/Eastern')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')

class LoadHandler(tornado.web.RequestHandler):
    def get(self):
        load = re.search('\d\.\d\d',
                         subprocess.check_output('uptime')).group()
        self.set_header('Access-Control-Allow-Origin', '*')
        self.write(json.dumps({
                'load': load,
                'timestamp': datetime.now(EST).isoformat()
            }))

class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        pids = []
        for proc in psutil.process_iter():
            p = proc.as_dict(attrs=['pid', 'name'])
            pids.append([p['name'], p['pid']])

        self.set_header('Access-Control-Allow-Origin', '*')
        self.write(json.dumps({
                'cpu': psutil.cpu_percent(interval=None),
                'cpus': psutil.cpu_count(),
                'disk': psutil.disk_usage('/'),
                'mem': psutil.virtual_memory(),
                'pids': pids,
                'timestamp': datetime.now(EST).isoformat()
            }))

class ShutdownHandler(tornado.web.RequestHandler):
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        if os.environ.get('MONITOR_TOKEN', ''):
            data = tornado.escape.json_decode(self.request.body)
            token = data.get('token', '')
            if os.environ['MONITOR_TOKEN'] == token:
                self.write(json.dumps({'shutdown': True}))
                os.system('sudo reboot now')
        else:
            self.write('')

application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/load.json', LoadHandler),
        (r'/stats.json', StatsHandler),
        (r'/shutdown', ShutdownHandler)

], debug=False)

if __name__ == "__main__":
    application.listen(5000, address='0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()
