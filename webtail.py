from tornado.websocket import WebSocketHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler
from tornado.web import Application
import threading
import queue
import os
import re,logging

fmt = "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(threadName)s %(message)s"
logging.basicConfig(level=logging.DEBUG,format=fmt)

q=queue.Queue()


class MainHandle(RequestHandler):
    def get(self,*args,**kwargs):
        HTML = '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>test</title>
            </head>
            <body>
                <input type="text" id="input"/>
                <button id="button">file</button>
                <pre id="text"></pre>
            <script>
                var ws = new WebSocket("ws://10.154.156.87:3003/ws")
                text = document.getElementById("text")
                input = document.getElementById("input")
                button = document.getElementById("button")
                button.onclick = function () {
                    ws.send(input.value)
                    text.innerHTML += ("实时" + input.value +"日志<br>")

                }
                ws.onmessage = function (message) {
                    text.innerHTML += message.data
                }

            </script>
            </body>
            </html>
        '''
        self.write(HTML)

class WebHandle(WebSocketHandler):
    work={}
    fd={}

    def on_message(self,message):
        path=message
        logging.info('###### -->{}'.format(message))
        if self.fd.pop(self.ws_connection,None) is not None:
            self.shutdown()
        if not re.match('/',path):
            raise Exception('{} is fault!'.format(path))
        

        e=threading.Event()
        t=threading.Thread(target=self.read_log,args=(path,e))
        self.work[self.ws_connection] = e
        self.fd[self.ws_connection] = path
        for i,e in self.work.items():
            print('{}==work==>{}'.format(i,e))
        for i,e in self.fd.items():
            print('{}==fd==>{}'.format(i,e))
        t.start()

    def on_connection_close(self):
        self.shutdown()

    def shutdown(self):
        event = self.work.pop(self.ws_connection,None)
        if event is not None:
            event.set()

    def read_log(self,path,e):
        offset = 0
        while not e.is_set():
            with open(path) as f:
                if offset > os.stat(path).st_size:
                    offset = 0
                f.seek(offset)
                #yield from f
                for line in f:
                    self.write_message(line)
                offset=f.tell()
            e.wait(0.1)

def source(q):
    for line in read_log(path):
        q.put(line)



def server(port):
    server=HTTPServer(app)
    server.listen(port,address='0.0.0.0')



if __name__ == '__main__':
    app = Application(
    [(r'/',MainHandle),
    (r'/ws',WebHandle)]
)
    server(3003)
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        IOLoop.current().stop()