import json
import subprocess
from textwrap import dedent
from flask import Flask, make_response, request

app = Flask(__name__)


class SpeedTestServer:
    def __init__(self, server_id, name, location, country):
        self.server_id = server_id
        self.name = name
        self.location = location
        self.country = country

    def __repr__(self):
        return f"{self.server_id}: {self.name} [{self.location}, {self.country}]"

    def metrics_link(self):
        return f'<a href="/metrics?server_id={self.server_id}">Metrics ({self.name} {self.country})</a>'

class SpeedTestException(Exception):
    pass

def speed_test(server_id=None):
    cmd = "speedtest --accept-license --format=json"
    if server_id is not None:
        cmd += f" --server-id={server_id}"

    print(cmd)
    res = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if res.returncode != 0:
        raise SpeedTestException(f'speedtest command failed.exit no zero. {res.stderr}')
    else:
        if len(res.stderr) > 0:
            print(f'speedtest command stderr:\n {res.stderr}')
        return json.loads(res.stdout)


def speed_test_server_list():
    cmd = "speedtest --servers --format=json"
    ret = []

    res = subprocess.run(cmd, capture_output=True, shell=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        raise SpeedTestException("speedtest command failed")

    for server in json.loads(res.stdout)['servers']:
        ret.append(SpeedTestServer(server['id'], server['name'], server['location'], server['country']))
    return ret


@app.route('/')
def index():
    return '<a href="/metrics">Metrics (auto)</a><br>' + '<br>'.join(
        [s.metrics_link() for s in speed_test_server_list()])


@app.route('/metrics', methods=['GET'])
def metrics():
    try:
        st = speed_test(request.args.get("server_id"))
        common_labels = f'country="{st["server"]["country"]}",id="{st["server"]["id"]}",name="{st["server"]["name"]}",ip="{st["server"]["ip"]}"'
        text = dedent(f"""
        # HELP speedtest_jitter.
        # TYPE speedtest_jitter counter
        speedtest_jitter{{{common_labels},type="ping"}} {st['ping']['jitter']}
        
        # HELP speedtest_latency.
        # TYPE speedtest_latency counter
        speedtest_latency{{{common_labels},type="ping"}} {st['ping']['latency']}
        speedtest_latency{{{common_labels},type="ping_low"}} {st['ping']['low']}
        speedtest_latency{{{common_labels},type="ping_high"}} {st['ping']['high']}
        speedtest_latency{{{common_labels},type="download_latency"}} {st['download']['latency']['jitter']}
        speedtest_latency{{{common_labels},type="download_iqm"}} {st['download']['latency']['iqm']}
        speedtest_latency{{{common_labels},type="download_low"}} {st['download']['latency']['low']}
        speedtest_latency{{{common_labels},type="download_high"}} {st['download']['latency']['high']}        
        speedtest_latency{{{common_labels},type="upload_latency"}} {st['upload']['latency']['jitter']}
        speedtest_latency{{{common_labels},type="upload_iqm"}} {st['upload']['latency']['iqm']}
        speedtest_latency{{{common_labels},type="upload_low"}} {st['upload']['latency']['low']}
        speedtest_latency{{{common_labels},type="upload_high"}} {st['upload']['latency']['high']}
        
        # HELP speedtest_bandwidth.
        # TYPE speedtest_bandwidth counter
        speedtest_bandwidth{{{common_labels},type="download"}} {st['download']['bandwidth']}
        speedtest_bandwidth{{{common_labels},type="upload"}} {st['upload']['bandwidth']}
        
        # HELP speedtest_bytes.
        # TYPE speedtest_bytes counter
        speedtest_bytes{{{common_labels},type="download"}} {st['download']['bytes']}
        speedtest_bytes{{{common_labels},type="upload"}} {st['upload']['bytes']}
        
        # HELP speedtest_elapsed.
        # TYPE speedtest_elapsed counter
        speedtest_elapsed{{{common_labels},type="download"}} {st['download']['elapsed']}
        speedtest_elapsed{{{common_labels},type="upload"}} {st['upload']['elapsed']}
        """)
        response = make_response(text, 200)
        response.mimetype = "text/plain"
    except Exception as e:
        print(f"error occurred: {e}")
        response = make_response(str(e), 500)
        response.mimetype = "text/plain"
    return response


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
