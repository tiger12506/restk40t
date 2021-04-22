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
        self.uris = []

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

    uri=''
    if ("uri0" in rest.uris):
        uri=rest.uris["uri0"]
    return rest.template.render(uri=uri)

@rest.app.route("/burn")
def burn():
    raster = '500'
    if ('raster' in request.args):
        raster = request.args['raster']
    cut = '20'
    if ('cut' in request.args):
        cut = request.args['cut']
    passes = '1'
    if ('passes' in request.args):
        passes = request.args['passes']

    rest.work.put("operation* delete")
    rest.work.put("element* delete")
    rest.work.put("raster -c #000000 -s {} mm/s -o 50".format(raster))
    rest.work.put("cut -c #ff0000 -s {} mm/s".format(cut))
    rest.work.put("rect 0 0 1cm 1cm stroke #ff0000")
    rest.work.put("rect 0.5mm 0.5mm 9mm 9mm fill #000000")
    rest.work.put("element* classify")

    rest.work.put("plan clear")
    rest.work.put("plan copy")
    rest.work.put("plan preprocess")
    rest.work.put("plan validate")
    rest.work.put("plan blob")
    rest.work.put("plan optimize")
    rest.work.put("start")
    rest.work.put("plan spool")

# Maybe these already exist in the plan
#    rest.work.put("move 0 0")
#    rest.work.put("unlock")
    return 'OK'

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

        # Retrieve camera URIs from meerk40t
        camera_setting = kernel.get_context("camera")
        rest.uris = camera_setting._kernel.load_persistent_string_dict(camera_setting._path, suffix=True)

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
