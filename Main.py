import dash

from lib.Frontend import Frontend


class Main:

    def __init__(self):
        """ (void) -> void
        Constructer of the Main class.
        Will initialize dash and frontend classes.
        """
        # initialize Dash
        app = dash.Dash(__name__, title = 'Wettermonitor')
        # instanciate Frontend
        self.frontend = Frontend(app)

    def run(self):
        """ (void) -> void
        Function to run the software.
        """
        # load user interface
        self.frontend.run()
        # start Dash server
        self.frontend.app.run_server(debug=False)

if __name__ == '__main__':
    # instanciate Main class
    main = Main()
    # Applikation starten
    main.run()
