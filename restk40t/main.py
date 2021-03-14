from flask import Flask, request, Response
from werkzeug.serving import make_server
from jinja2 import Environment, PackageLoader, select_autoescape
import threading
import time
import queue

class RestK40t(object):
    def __init__(self):
        self.work = queue.Queue()
        self.context = None
        self.app = Flask(__name__)
        self.server = make_server('0.0.0.0', 4000, self.app) 
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.quit = False

        self.env = Environment(
                loader=PackageLoader('restk40t.main', 'templates'),
                autoescape=select_autoescape(['html', 'xml']),
                line_statement_prefix='#'
        )
        self.template = self.env.get_template('index.html')

rest = RestK40t()

@rest.app.route("/")
def console():
    if ('cmd' in request.args):
      rest.work.put(request.args['cmd'])
      return 'OK'
    return rest.template.render()


def plugin(kernel, lifecycle):
    if lifecycle == 'register':
        """
        Register our changes to meerk40t. These should modify the registered values within meerk40t or install different
        modules and modifiers to be used in meerk40t.
        """
        pass
    elif lifecycle == 'boot':
        """
        Do some persistent actions or start modules and modifiers. Register any scheduled tasks or threads that need
        to be running for our plugin to work. 
        """
        pass
    elif lifecycle == 'ready':
        """
        Start process running. Sometimes not all modules and modifiers will be ready as they are processed in order
        during boot. If your thread or work depends on other parts of the system being fully established they should 
        work here.
        """

        rest.context = kernel.get_context("/")

        def run():
            rest.server.serve_forever()

        def do_work():
            while not rest.quit:
                try:
                    cmd = rest.work.get(False)
                    rest.context(cmd+'\r\n')
                except queue.Empty:
                    pass
                time.sleep(0.1)

        rest.context.threaded(run, thread_name="FlaskWebServer")
        rest.context.threaded(do_work, thread_name="FlaskHandler")

    elif lifecycle == 'mainloop':
        """
        This is the start of the gui and will capture the default thread as gui thread. If we are writing a new gui
        system and we need this thread to do our work. It should be captured here. This is the main work of the program. 
        """
        pass
    elif lifecycle == 'shutdown':
        """
        Meerk40t's closing down, our plugin should adjust accordingly. All registered meerk40t processes will be stopped
        any plugin processes should also be stopped so the program can close correctly.
        """
        rest.quit = True
        rest.server.shutdown()
