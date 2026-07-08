#!/usr/bin/env python3
import socketserver
import socket
import struct
import signal
import sys
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE

# Import our modules
from blocklist import Blocklist
from cache import DNSCache
from stats import Stats
from config import config

# ---------- Load configuration ----------
PORT = config.get('server.port', 5353)
BIND_ADDRESS = config.get('server.bind_address', '0.0.0.0')

# Upstream DNS resolvers (supporting list of IPs)
upstream_list = config.get('upstream_dns', ['8.8.8.8'])
UPSTREAM_RESOLVERS = []
for ip in upstream_list:
    ip = ip.strip()
    if ip:
        UPSTREAM_RESOLVERS.append((ip, 53))

CACHE_SIZE = config.get('cache.max_size', 5000)
CACHE_TTL = config.get('cache.default_ttl', 300)
STATS_FILE = config.get('stats.save_file', 'stats.json')
BLOCKLIST_URLS = config.get('blocklists', [
    'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts'
])

# ---------- Initialize components ----------
print("Loading blocklists...")
blocklist = Blocklist()
for url in BLOCKLIST_URLS:
    blocklist.load_from_url(url)

cache = DNSCache(max_size=CACHE_SIZE, default_ttl=CACHE_TTL)
stats = Stats(save_file=STATS_FILE)

# ---------- Graceful shutdown ----------
def handle_shutdown(signum, frame):
    print("\n🛑 Shutting down gracefully...")
    stats.save()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# ---------- DNS request handler ----------
class BlockingHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, client_sock = self.request

        try:
            request = DNSRecord.parse(data)

            # Malformed query without a question section
            if request.q is None:
                client_sock.sendto(b"", self.client_address)
                return

            qname = str(request.q.qname).rstrip('.')
            qtype = request.q.qtype
            original_id = request.header.id

            # ----- 1. Check cache -----
            cached_response = cache.get(qname, qtype)
            if cached_response is not None:
                # Fix the ID to match the current query
                fixed_response = struct.pack('!H', original_id) + cached_response[2:]
                client_sock.sendto(fixed_response, self.client_address)
                stats.log_query(qname, blocked=False, cached=True)
                return

            # ----- 2. Check blocklist -----
            if blocklist.is_blocked(qname):
                print(f"🔴 BLOCKED: {qname}")
                reply = DNSRecord(
                    DNSHeader(id=original_id, qr=1, aa=1, ra=1),
                    q=request.q
                )
                reply.add_answer(
                    RR(qname, rtype=QTYPE.A, rclass=1, ttl=60, rdata=A("0.0.0.0"))
                )
                response_packet = reply.pack()
                client_sock.sendto(response_packet, self.client_address)
                stats.log_query(qname, blocked=True, cached=False)
                return

            # ----- 3. Forward to upstream -----
            print(f"🔄 Forwarding: {qname}")
            response = None
            for resolver_ip, resolver_port in UPSTREAM_RESOLVERS:
                proxy = None
                try:
                    family = socket.AF_INET6 if ":" in resolver_ip else socket.AF_INET
                    proxy = socket.socket(family, socket.SOCK_DGRAM)
                    proxy.settimeout(2.0)
                    proxy.sendto(data, (resolver_ip, resolver_port))
                    response, _ = proxy.recvfrom(4096)
                    break  # Success, exit the resolver loop
                except (socket.timeout, socket.error) as e:
                    print(f"⚠️ Warning: Upstream resolver {resolver_ip}:{resolver_port} failed: {e}")
                finally:
                    if proxy:
                        proxy.close()

            if response is None:
                raise Exception("All upstream DNS resolvers timed out or failed.")

            # Record stats for successful forwarded resolution
            stats.log_query(qname, blocked=False, cached=False)

            # ----- 4. Cache the response (extract TTL) -----
            ttl = None
            try:
                resp = DNSRecord.parse(response)
                if resp.rr:
                    ttl = min(rr.ttl for rr in resp.rr)
            except:
                pass
            cache.set(qname, qtype, response, ttl)
            print(f"📦 Cached response for {qname} (TTL: {ttl or 'default'})")

            client_sock.sendto(response, self.client_address)

        except Exception as e:
            print(f"❌ ERROR in handler: {e}")
            import traceback
            traceback.print_exc()

# ---------- Main entry point ----------
if __name__ == "__main__":
    server = socketserver.UDPServer((BIND_ADDRESS, PORT), BlockingHandler)
    print(f"DNS blocker running on {BIND_ADDRESS}:{PORT}")
    print("Press Ctrl+C to stop and save stats.")
    server.serve_forever()
