import cgi
import pickle
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json
import os
import tarfile
import time

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def error(self, err):
        ''' Send the given error message as response'''
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Error: ' + err.encode())
        print(b"Error: %s" % err.encode())

    def do_GET(self):
        print(self)
        if self.path == '/leaderboard' or self.path == '/' or self.path == '':
            self.leaderboard()
        elif self.path.split('/')[1] == 'images':
            self.images()
        else:
            self.error('Unknown Path "%s"' % self.path)

    def do_POST(self):
        print(self)
        if self.path == '/upload_file':
            self.upload_file()
        elif self.path == '/register_team':
            self.register_team()
        else:
            self.error('Unknown Path "%s"' % self.path)

    def images(self):
        path = os.path.join(data_dir, *self.path.split('/')[2:])
        with open(path, 'rb') as file:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(file.read())

    def leaderboard(self):
        # Sort the scores
        sorted = [(scores[x][0], x) for x in scores]
        sorted.sort(key=lambda x: x[0], reverse=True)

        # Prepare HTML for the list
        html_list = ""
        for id, (avgscore, team) in enumerate(sorted):
            # Prepare HTML for sublist of scores of individual experiments
            html_sublist = ""
            expts = scores[team][1]
            expts.sort(key=lambda x: x[0])
            for expt, dat in expts:
                imgdir = os.path.join('images', team, expt + '.png')
                html_sublist += '''
                <tr>
                    <th scope="row">{expt}</th>
                    <td>{d[avg_net_qoe]:.3}</td>
                    <td>{d[avg_quality_score]:.3}</td>
                    <td>{d[avg_rebuf_penalty]:.3}</td>
                    <td>{d[avg_smoothness_penalty]:.3}</td>
                    <td><a href="{imgdir}">view graph</a></td>
                </tr>
                '''.format(
                    expt=expt,
                    imgdir=imgdir,
                    d=dat
                )

            html_list += '''
<li class="list-group-item">
        <div class="row">
            <div class="col-4"><a class="btn btn-link" data-toggle="collapse" href="#coll{id}" role="button" aria-expanded="false" aria-controls="coll{id}">{avgscore:.3}</a></div>
            <div class="col-8"><a class="btn btn-link" data-toggle="collapse" href="#coll{id}" role="button" aria-expanded="false" aria-controls="coll{id}">{team}</a></div>
        </div>

    <div id="coll{id}" class="collapse">
        <table class="table">
            <thead><tr>
                <th scope="col">Experiment</th>
                <th scope="col">Score</th>
                <th scope="col">Avg. Quality</th>
                <th scope="col">Avg. Rebuffer Penalty</th>
                <th scope="col">Avg. Smoothness Penalty</th>
                <th scope="col">Graph</th>
            </tr></thead>
            <tbody>
                {html_sublist}
            </tbody>
        </table>
    </div>
</li>
        '''.format(id=id, team=team, avgscore=avgscore, html_sublist=html_sublist)

        # Prepare full string
        html_full = '''
<html>
<head>
  <title>6.829 Pset2 Leaderboard</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
  <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
</head>
<body>
  <div class="container-fluid">
      <h1>6.829 Problem Set 2 Leaderboard</h1>

      <ul class="list-group">
      <li class="list-group-item">
        <div class="row">
            <div class="col-4"><h4>Average Score</h4></div>
            <div class="col-8"><h4>Team Name</h4></div>
        </div>

        {list}
      </ul>
  </div>
</body>
</html>
        '''.format(list=html_list)

        # Send the generated page
        self.send_response(200)
        self.end_headers()
        self.wfile.write(html_full.encode())

    def upload_file(self):
        # Get form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        team = form.getvalue('team')
        # If team is not registered, send error
        if team not in teams:
            self.error('Team "%s" not registered' % team)
            print(teams)
            return

        # Save the file
        fname = os.path.join(data_dir, team, str(int(time.time())) + '.tar.gz')
        with open(fname, 'wb') as f:
            f.write(form.getvalue('results'))

        tar = tarfile.open(fname, mode='r')

        # Determine which experiments are present in this
        expts = []
        for member in tar:
            name = os.path.normpath(member.name)
            name = name.split('/')
            if len(name) != 4:
                continue
            expts.append('/'.join(name[0:4]))

        if len(expts) == 0:
            if len(name) == 1:
                self.error('Error reading tarfile. No subdirectories found')
                return

        # Extract results from the experiments
        results = []
        for expt in expts:
            # Get the results json
            rfname = os.path.join(expt, 'results.json')
            rfile = tar.extractfile(rfname)
            result = json.load(rfile)
            expt_name = expt.split('/')[-1]
            results.append((expt_name, result))

            # Extract the graph
            imgname = os.path.join(expt, 'buffer-bitrate-throughput.png')
            with open(os.path.join(data_dir, team, expt_name + '.png'), 'wb') as imgout:
                imgout.write(tar.extractfile(imgname).read())

        avg_score = sum([x[1]['avg_net_qoe'] for x in results]) / len(results)

        # Save the results
        scores[team] = (avg_score, results)
        with open(os.path.join(data_dir, 'scores'), 'wb') as f:
            pickle.dump(scores, f)

        self.send_response(200)
        self.end_headers()

        self.wfile.write(b'Received results')

    def register_team(self):
        # Get form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        # Team name
        team = form.getvalue('team')
        members = form.getlist('members')

        if team is None:
            self.error('Team name not specified')
            return
        if len(members) == 0:
            self.error('Team must have at least one member')
            return

        if team in teams:
            self.error('Team "%s" already registered. Members are %s' % (team, json.dumps(teams[team])))
            return

        teams[team] = members
        os.mkdir(os.path.join(data_dir, team))

        with open(os.path.join(data_dir, 'teams'), 'wb') as f:
            pickle.dump(teams, f)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(('Registered: ' + team + ' ' + json.dumps(members)).encode())

# Load data from files
data_dir = 'server_data/'

# Dictionary of team names registered. Contains list of team members
try:
    with open(os.path.join(data_dir, 'teams'), 'rb') as f:
        teams = pickle.load(f)
except:
    teams = {}

# Dictionary of scores indexed by team
try:
    with open(os.path.join(data_dir, 'scores'), 'rb') as f:
        scores = pickle.load(f)
except:
    scores = {}

httpd = HTTPServer(('localhost', 8888), SimpleHTTPRequestHandler)
httpd.serve_forever()
