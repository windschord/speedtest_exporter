import json
import re
import subprocess
from textwrap import dedent
from flask import Flask, make_response, request

app = Flask(__name__)


class SpeedTestServer:
    def __init__(self, id, name, location, country, distance):
        self.id = id
        self.name = name
        self.location = location
        self.country = country
        self.distance = distance

    def __repr__(self):
        return f"{self.id}: {self.name} [{self.location}, {self.country}] {self.distance}km"

    def metrics_link(self):
        return f'<a href="/metrics?server_id={self.id}">Metrics ({self.name} {self.country} {self.distance}km)</a>'


def speed_test(server_id=None):
    cmd = ["speedtest", "--json"]
    if server_id is not None:
        cmd.append("--server")
        cmd.append(server_id)

    print(cmd)
    res = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if res.returncode != 0:
        raise Exception(f'speedtest command failed.exit no zero. {res.stderr}')
    elif len(res.stderr) > 0:
        raise Exception(f'speedtest command failed {res.stderr}')
    else:
        return json.loads(res.stdout)


def speed_test_server_list():
    cmd = ["speedtest", "--list", "--json"]
    fmt = re.compile(r'(\d+)\) (.*) \((.*), (.*)\) \[(.*) km\]')
    ret = []

    res = subprocess.run(cmd, capture_output=True, shell=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        raise Exception("speedtest command failed")

    for line in res.stdout.split('\n'):
        if len(line.strip()) == 0:
            continue

        trimmed = fmt.findall(line)
        if len(trimmed[0]) != 5:
            print(f"invalid line. not 5 rows: {line}")
            continue
        ret.append(SpeedTestServer(trimmed[0][0], trimmed[0][1], trimmed[0][2], trimmed[0][3], trimmed[0][4]))
    return ret


@app.route('/')
def index():
    return '<a href="/metrics">Metrics (auto)</a><br>' + '<br>'.join([s.metrics_link() for s in speed_test_server_list()])


@app.route('/metrics', methods=['GET'])
def metrics():
    try:
        st = speed_test(request.args.get("server_id"))

        text = dedent(f"""
        # HELP speed_test_ping The number of ping (ms).
        # TYPE speed_test_ping counter
        speed_test_ping{{country="{st["server"]["country"]}",id="{st["server"]["id"]}",host="{st["server"]["host"]}"}} {st["ping"]}
        # HELP speed_test_download The number of download (bit/s).
        # TYPE speed_test_download counter
        speed_test_download{{country="{st["server"]["country"]}",id="{st["server"]["id"]}",host="{st["server"]["host"]}"}} {st["download"]}
        # HELP speed_test_upload The number of upload (bit/s).
        # TYPE speed_test_upload counter
        speed_test_upload{{country="{st["server"]["country"]}",id="{st["server"]["id"]}",host="{st["server"]["host"]}"}} {st["upload"]}
        """)
        response = make_response(text, 200)
        response.mimetype = "text/plain"
    except Exception as e:
        response = make_response(str(e), 500)
        response.mimetype = "text/plain"
    return response


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
