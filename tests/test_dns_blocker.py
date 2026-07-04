import socket
import threading
import time
import pytest
from dnslib import DNSRecord, QTYPE
import socketserver

# Import handler and components from dns_blocker
from dns_blocker import BlockingHandler, blocklist, cache

def test_dns_blocker_handler():
    # Setup UDPServer on an ephemeral port (port 0 selects a free high port)
    server = socketserver.UDPServer(('127.0.0.1', 0), BlockingHandler)
    ip, port = server.server_address
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # ---------- Test 1: Blocked Domain Resolution ----------
        blocklist.domains.add("blocked-test.com")
        
        q = DNSRecord.question("blocked-test.com")
        request_packet = q.pack()
        
        # Send DNS query via UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(request_packet, (ip, port))
        
        response, _ = sock.recvfrom(4096)
        reply = DNSRecord.parse(response)
        
        # Assert it was resolved to 0.0.0.0 because it's blocked
        assert len(reply.rr) == 1
        assert str(reply.rr[0].rdata) == "0.0.0.0"
        
        # ---------- Test 2: Cached Domain Resolution ----------
        # Construct a dummy response to cache
        dummy_reply = DNSRecord.question("cached-test.com")
        dummy_packet = dummy_reply.pack()
        cache.set("cached-test.com", QTYPE.A, dummy_packet, ttl=60)
        
        q_cached = DNSRecord.question("cached-test.com")
        request_packet_cached = q_cached.pack()
        
        sock.sendto(request_packet_cached, (ip, port))
        response_cached, _ = sock.recvfrom(4096)
        
        # Assert response is returned
        assert response_cached is not None
        
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()
