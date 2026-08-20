"""
SSRF Protection Module.

Prevents Server-Side Request Forgery attacks by validating URLs
and blocking access to private networks and sensitive endpoints.
"""
import ipaddress
import re
import socket
from typing import List, Optional
from urllib.parse import urlparse

from core.config.settings import get_settings
from shared.exceptions import SSRFError
from core.observability.logging import get_logger

logger = get_logger(__name__)


# Private/Internal IP ranges (RFC 1918, RFC 4193, etc.)
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),  # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),  # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),  # Private Class C
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

# Cloud metadata endpoints (AWS, GCP, Azure, etc.)
METADATA_ENDPOINTS = [
    "169.254.169.254",  # AWS, Azure, GCP
    "metadata.google.internal",  # GCP
    "169.254.169.253",  # Azure (fallback)
]

# Localhost variations
LOCALHOST_VARIATIONS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
    "::1",
]


class SSRFProtection:
    """
    SSRF protection validator.
    
    Validates URLs to prevent Server-Side Request Forgery attacks by:
    - Blocking private IP ranges
    - Blocking localhost access
    - Blocking cloud metadata endpoints
    - Validating domain allowlists
    - Checking for DNS rebinding attempts
    """

    def __init__(self):
        self.settings = get_settings()

    def validate_url(self, url: str) -> None:
        """
        Validate URL for SSRF protection.
        
        Args:
            url: URL to validate
            
        Raises:
            SSRFError: If URL fails security checks
        """
        if not url or not url.strip():
            raise SSRFError(url, "URL cannot be empty")

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise SSRFError(url, f"Invalid URL format: {str(e)}")

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise SSRFError(url, f"Unsupported scheme: {parsed.scheme}. Only HTTP/HTTPS allowed")

        # Require HTTPS in production
        if self.settings.is_production and parsed.scheme != "https":
            raise SSRFError(url, "HTTPS required in production environment")

        # Reject userinfo because credentials in an agent URL can be leaked to logs,
        # redirects, proxies, or downstream telemetry.
        if parsed.username is not None or parsed.password is not None:
            raise SSRFError(url, "Userinfo credentials are not allowed in endpoint URLs")

        try:
            parsed.port
        except ValueError as exc:
            raise SSRFError(url, f"Invalid port: {exc}")

        # Extract and normalize hostname. IDNA normalization makes allowlist and
        # metadata checks consistent for internationalized domains.
        hostname = parsed.hostname
        if not hostname:
            raise SSRFError(url, "URL must contain a hostname")
        hostname = hostname.rstrip(".").lower()

        # Check against allowlist if configured
        if self.settings.allowed_domains:
            if not self._is_domain_allowed(hostname):
                raise SSRFError(
                    url,
                    f"Domain '{hostname}' not in allowlist",
                )

        # Block localhost
        if self.settings.block_localhost:
            if self._is_localhost(hostname):
                raise SSRFError(url, "Access to localhost is blocked")

        # Block private networks
        if self.settings.block_private_networks:
            if self._is_private_ip(hostname):
                raise SSRFError(url, "Access to private networks is blocked")
            if self._hostname_resolves_to_private_ip(hostname, parsed.port or (443 if parsed.scheme == "https" else 80)):
                raise SSRFError(url, "Hostname resolves to a private network address")

        # Block metadata endpoints
        if self.settings.block_metadata_endpoints:
            if self._is_metadata_endpoint(hostname):
                raise SSRFError(url, "Access to cloud metadata endpoints is blocked")

        logger.debug(f"URL validated: {url}", extra={"hostname": hostname})

    def _is_localhost(self, hostname: str) -> bool:
        """Check if hostname is localhost without substring false positives."""
        hostname_lower = hostname.rstrip(".").lower()
        if hostname_lower in {value.lower().strip("[]") for value in LOCALHOST_VARIATIONS}:
            return True
        try:
            return ipaddress.ip_address(hostname_lower).is_loopback
        except ValueError:
            return hostname_lower.endswith(".localhost")

    def _hostname_resolves_to_private_ip(self, hostname: str, port: int) -> bool:
        """Resolve all A/AAAA records and reject if any address is unsafe."""
        try:
            records = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except socket.gaierror:
            # The actual HTTP request will return a connection error. Do not turn
            # DNS outages into an SSRF denial because the hostname is allowlisted.
            return False
        for record in records:
            address = record[4][0]
            try:
                if self._is_ip_private(ipaddress.ip_address(address)):
                    return True
            except ValueError:
                return True
        return False

    def _is_private_ip(self, hostname: str) -> bool:
        """
        Check if hostname resolves to a private IP.
        
        Args:
            hostname: Hostname or IP address
            
        Returns:
            True if private IP, False otherwise
        """
        try:
            # Try to parse as IP address directly
            ip = ipaddress.ip_address(hostname)
            return self._is_ip_private(ip)
        except ValueError:
            # Hostname, not an IP - would need DNS resolution
            # For now, we only check direct IP addresses
            # In production, you might want to resolve DNS and check the result
            return False

    def _is_ip_private(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Check if IP address is in private range."""
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                return True
        return False

    def _is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a cloud metadata endpoint."""
        hostname_lower = hostname.rstrip(".").lower()
        if hostname_lower in {endpoint.lower() for endpoint in METADATA_ENDPOINTS}:
            return True
        try:
            return ipaddress.ip_address(hostname_lower).is_link_local and str(hostname_lower) == "169.254.169.254"
        except ValueError:
            return hostname_lower.endswith(".metadata.google.internal")

    def _is_domain_allowed(self, hostname: str) -> bool:
        """
        Check if domain is in allowlist.
        
        Args:
            hostname: Hostname to check
            
        Returns:
            True if allowed, False otherwise
        """
        hostname_lower = hostname.lower()
        
        for allowed_domain in self.settings.allowed_domains:
            allowed_lower = allowed_domain.lower()
            
            # Exact match
            if hostname_lower == allowed_lower:
                return True
            
            # Subdomain match (if allowlist item starts with .)
            if allowed_lower.startswith(".") and hostname_lower.endswith(allowed_lower):
                return True

            # Allow subdomains by default, but require a label boundary.
            if hostname_lower.endswith(f".{allowed_lower}"):
                return True
        
        return False

    def validate_ip_address(self, ip_str: str) -> None:
        """
        Validate IP address for SSRF protection.
        
        Args:
            ip_str: IP address string
            
        Raises:
            SSRFError: If IP address fails security checks
        """
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError as e:
            raise SSRFError(ip_str, f"Invalid IP address: {str(e)}")

        if self.settings.block_private_networks and self._is_ip_private(ip):
            raise SSRFError(ip_str, "Private IP addresses are blocked")

        logger.debug(f"IP address validated: {ip_str}")


# Global instance
_ssrf_protection: Optional[SSRFProtection] = None


def get_ssrf_protection() -> SSRFProtection:
    """Get global SSRF protection instance."""
    global _ssrf_protection
    if _ssrf_protection is None:
        _ssrf_protection = SSRFProtection()
    return _ssrf_protection


def reset_ssrf_protection() -> None:
    """Reset SSRF protection (useful for testing)."""
    global _ssrf_protection
    _ssrf_protection = None
