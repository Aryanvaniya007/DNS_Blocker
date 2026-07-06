# 📐 DNS Blocker & Web Dashboard: Architectural Explanation

This document provides a detailed walkthrough of all the files in this project, explaining **how they work** and **why they were designed/implemented** this way.

---

## 📂 File Directory Overview

```text
dns-blocker/
├── dns_blocker.py      # The main DNS UDP server (orchestrator)
├── blocklist.py        # Blocklist loader and domain filter
├── cache.py            # In-memory DNS cache with TTL management
├── stats.py            # Metrics logger and persistence layer
├── config.py           # Configuration reader
├── config.yaml         # Configuration parameters (YAML)
├── dashboard.py        # Flask-based web dashboard
├── Dockerfile          # Docker container configuration
└── docker-compose.yml  # Multi-container service definition
```

---

## 🧩 Detailed File Explanations

### 1. `dns_blocker.py` (Core Server)
* **How it works:**
  It utilizes Python's built-in `socketserver.UDPServer` to run a UDP server listening on port 53. When a query is received:
  1. It parses the raw UDP payload into a `dnslib.DNSRecord`.
  2. It queries the cache (`cache.py`). If found, it returns the cached response immediately.
  3. It checks the blocklist (`blocklist.py`). If the domain is blocked, it constructs a fake DNS reply pointing to `0.0.0.0` (sinkhole) and returns it.
  4. If not blocked, it forwards the query to an upstream DNS server (`8.8.8.8` or a local nameserver), caches the response, and returns it to the client.
* **Why it was done this way:**
  DNS operates primarily over UDP (port 53) because it requires fast, low-overhead communication. Using a socket server ensures high throughput, while `dnslib` avoids manually crafting binary DNS packets.

---

### 2. `blocklist.py` (Domain Filtering)
* **How it works:**
  Downloads remote host lists (like StevenBlack's hosts) via `urllib.request`. It parses the files line-by-line, ignores comments, and extracts domains mapped to `0.0.0.0` or `127.0.0.1`. These are loaded into a Python `set`.
* **Why it was done this way:**
  A Python `set` uses hash tables, giving it an **$O(1)$** lookup complexity. This means verifying if a domain is blocked takes constant time, regardless of whether there are 10 domains or 100,000 domains.

---

### 3. `cache.py` (DNS Cache)
* **How it works:**
  It implements a custom in-memory key-value cache where the keys are a combination of `(domain_name, query_type)` and the values are `(dns_response_bytes, expiration_timestamp)`.
* **Why it was done this way:**
  Without caching, every query must go to the upstream DNS, introducing latency (often 50–150ms). Caching responses locally drops lookup times to **0ms** for repeated queries. It extracts the TTL (Time to Live) from the upstream response to ensure it only caches records for as long as they are valid.

---

### 4. `stats.py` (Metrics & Analytics)
* **How it works:**
  Captures logs for every request (domain, status: blocked/cached/forwarded, timestamp). It periodically aggregates this data into total query counts, blocking rates, cache hit rates, top blocked domains, and a hourly timeline. It saves this information to `stats.json` on shutdown.
* **Why it was done this way:**
  To provide analytics without requiring a heavyweight database (like PostgreSQL or MySQL), it stores stats in a lightweight JSON format that can be easily loaded/written using Python's native `json` library.

---

### 5. `config.py` & `config.yaml` (Configurations)
* **How it works:**
  `config.yaml` declares environment variables, ports, upstream resolvers, and blocklists. `config.py` reads this YAML file and provides a helper class to fetch values safely with defaults.
* **Why it was done this way:**
  Separating configuration from code prevents hardcoding values. If you want to change the upstream DNS or add another blocklist, you only edit `config.yaml` without touching the Python code.

---

### 6. `dashboard.py` (Web Dashboard)
* **How it works:**
  A Flask-based web application that reads the metrics tracked by `stats.py` and renders them in a clean, simple HTML/CSS dashboard using a single endpoint. It auto-refreshes every 5 seconds.
* **Why it was done this way:**
  Flask is lightweight and ideal for microservices. Storing the HTML template as a string inside the file simplifies distribution, making it run with zero external static file dependencies.

---

### 7. `Dockerfile` & `docker-compose.yml` (Containerization)
* **How it works:**
  - `Dockerfile` packages the Python script, system utilities, and dependencies into a slim Linux image (`python:3.11-slim`).
  - `docker-compose.yml` coordinates two services: `dns-blocker` (UDP DNS server) and `dashboard` (Flask web server). They share a Docker Volume (`dns-data`) to read/write the `stats.json` file.
* **Why it was done this way:**
  Docker guarantees the project runs exactly the same way on any machine (Windows, Mac, Linux) without manual Python installation or dependency conflicts. Sharing a volume ensures the Flask dashboard can read live stats from the DNS blocker service seamlessly.

---

## 🔄 End-to-End Data Flow

```text
[Client query: doubleclick.net]
       │
       ▼
┌──────────────┐      Found?
│  dns_blocker │ ───────────────► [Cache Check]
└──────────────┘                       │ No
       │                               ▼
       │                       [Blocklist Check]
       │                               │ Yes (Blocked domain)
       ▼                               ▼
[Return 0.0.0.0] ◄─────────────── [Sinkhole Response]
```
