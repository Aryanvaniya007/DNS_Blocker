import requests

class Blocklist:
    def __init__(self):
        self.domains = set()
    
    def load_from_url(self, url):
        print(f"Loading blocklist from: {url}")
        try:
            response = requests.get(url, timeout=10)
            for line in response.text.split('\n'):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Handle hosts format: "0.0.0.0 example.com" or "127.0.0.1 example.com"
                if line.startswith('0.0.0.0') or line.startswith('127.0.0.1'):
                    parts = line.split()
                    if len(parts) >= 2:
                        domain = parts[1].strip().lower()
                        if domain and not domain.startswith('#'):
                            self.domains.add(domain)
                # Handle EasyList format: "||example.com^"
                elif line.startswith('||') and '^' in line:
                    domain = line[2:line.index('^')].lower()
                    self.domains.add(domain)
            print(f"Loaded {len(self.domains)} blocked domains")
        except Exception as e:
            print(f"Error loading blocklist: {e}")
    
    def is_blocked(self, domain):
        domain = domain.lower().rstrip('.')
        # Exact match
        if domain in self.domains:
            return True
        # Subdomain check (blocks ads.example.com if example.com is blocked)
        for blocked in self.domains:
            if domain.endswith('.' + blocked):
                return True
        return False

# Quick test when run directly
if __name__ == "__main__":
    bl = Blocklist()
    bl.load_from_url("https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts")
    print(f"Total domains: {len(bl.domains)}")
    print("Test blocked:", bl.is_blocked("doubleclick.net"))
