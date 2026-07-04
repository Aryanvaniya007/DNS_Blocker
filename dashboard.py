#!/usr/bin/env python3
from flask import Flask, jsonify, render_template_string
from stats import Stats
from config import config

stats = Stats(save_file=config.get('stats.save_file', 'stats.json'))

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DNS Blocker Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f4f4f4; }
        .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .stat-label { color: #555; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; }
        .badge-green { background: #28a745; color: white; }
        .badge-red { background: #dc3545; color: white; }
        .refresh { margin-top: 20px; }
    </style>
</head>
<body>
<div class="container">
    <h1>📊 DNS Blocker Dashboard</h1>
    <div class="stat-grid">
        <div class="stat-card"><div class="stat-number">{{ data.total_queries }}</div><div class="stat-label">Total Queries</div></div>
        <div class="stat-card"><div class="stat-number">{{ data.blocked }}</div><div class="stat-label">Blocked</div></div>
        <div class="stat-card"><div class="stat-number">{{ data.block_rate }}%</div><div class="stat-label">Block Rate</div></div>
        <div class="stat-card"><div class="stat-number">{{ data.cache_hit_rate }}%</div><div class="stat-label">Cache Hit Rate</div></div>
        <div class="stat-card"><div class="stat-number">{{ data.uptime // 3600 }}h {{ (data.uptime % 3600) // 60 }}m</div><div class="stat-label">Uptime</div></div>
    </div>
    <h2>🏆 Top Blocked Domains</h2>
    <table>
        <tr><th>#</th><th>Domain</th><th>Count</th></tr>
        {% for domain, count in data.top_10 %}
        <tr><td>{{ loop.index }}</td><td>{{ domain }}</td><td>{{ count }}</td></tr>
        {% else %}
        <tr><td colspan="3">No blocks yet.</td></tr>
        {% endfor %}
    </table>
    <h2>📈 Query Timeline (Last 24 hours)</h2>
    <table>
        <tr><th>Hour</th><th>Queries</th></tr>
        {% for hour, count in data.timeline.items() %}
        <tr><td>{{ hour }}</td><td>{{ count }}</td></tr>
        {% else %}
        <tr><td colspan="2">No data yet.</td></tr>
        {% endfor %}
    </table>
    <p class="refresh"><small>Auto-refreshes every 5 seconds.</small></p>
</div>
<script>
    setTimeout(function(){ location.reload(); }, 5000);
</script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    summary = stats.get_summary()
    return render_template_string(HTML_TEMPLATE, data=summary)

@app.route('/api/stats')
def api_stats():
    return jsonify(stats.get_summary())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
