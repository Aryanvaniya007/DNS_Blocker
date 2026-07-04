import yaml
import os

# Map config paths to environment variable overrides
ENV_MAPPING = {
    'server.port': ('DNS_PORT', int),
    'server.bind_address': ('DNS_BIND', str),
    'upstream_dns': ('UPSTREAM_DNS', lambda v: [x.strip() for x in v.split(',')]),
    'cache.max_size': ('CACHE_MAX_SIZE', int),
    'cache.default_ttl': ('CACHE_DEFAULT_TTL', int),
    'dashboard.enabled': ('DASHBOARD_ENABLED', lambda v: v.lower() in ('true', '1', 'yes')),
    'dashboard.port': ('DASHBOARD_PORT', int),
    'dashboard.host': ('DASHBOARD_HOST', str),
    'stats.save_file': ('STATS_FILE', str),
}

class Config:
    def __init__(self, config_path='config.yaml', config_data=None):
        """
        config_data: optional dict to use directly (for testing)
        """
        self.config_path = config_path
        if config_data is not None:
            self.data = config_data
        else:
            self.data = self._load()

    def _load(self):
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file {self.config_path} not found. Using defaults.")
            return self._defaults()
        except yaml.YAMLError as e:
            print(f"❌ Error parsing config: {e}")
            return self._defaults()

    def _defaults(self):
        return {
            'server': {'port': 5353, 'bind_address': '0.0.0.0'},
            'upstream_dns': ['8.8.8.8', '1.1.1.1'],
            'blocklists': ['https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts'],
            'cache': {'max_size': 5000, 'default_ttl': 300},
            'logging': {'level': 'INFO', 'file': '/var/log/dns_blocker.log'},
            'dashboard': {'enabled': True, 'port': 8080, 'host': '0.0.0.0'},
            'stats': {'save_file': 'stats.json'}
        }

    def get(self, key_path, default=None):
        """Retrieve a config value using dot notation (e.g., 'server.port') with env overrides."""
        # 1. Check environment variable override
        if key_path in ENV_MAPPING:
            env_var, cast_func = ENV_MAPPING[key_path]
            if env_var in os.environ:
                try:
                    return cast_func(os.environ[env_var])
                except Exception as e:
                    print(f"⚠️ Error casting env var {env_var}: {e}. Falling back to config file.")

        # 2. Check config file
        keys = key_path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

# Global instance
config = Config()

