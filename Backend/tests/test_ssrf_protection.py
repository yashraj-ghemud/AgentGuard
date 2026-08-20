"""Adversarial tests for endpoint URL validation."""

from unittest.mock import patch

import pytest

from core.execution.ssrf_protection import SSRFProtection
from shared.exceptions import SSRFError


@pytest.fixture
def protection():
    return SSRFProtection()


def test_rejects_userinfo_in_endpoint(protection):
    with pytest.raises(SSRFError, match="Userinfo"):
        protection.validate_url("https://user:password@example.com/agent")


def test_rejects_private_literal_ipv4(protection):
    with pytest.raises(SSRFError, match="localhost"):
        protection.validate_url("http://127.0.0.1:8000/run")


def test_rejects_dns_name_resolving_to_private_ip(protection):
    records = [(None, None, None, None, ("10.0.0.42", 443))]
    with patch("core.execution.ssrf_protection.socket.getaddrinfo", return_value=records):
        with pytest.raises(SSRFError, match="resolves to a private"):
            protection.validate_url("https://agent.example.com/run")


def test_allows_public_dns_name_when_all_resolved_addresses_are_public(protection):
    records = [(None, None, None, None, ("93.184.216.34", 443))]
    with patch("core.execution.ssrf_protection.socket.getaddrinfo", return_value=records):
        protection.validate_url("https://agent.example.com/run")


def test_metadata_hostname_requires_label_boundary(protection):
    assert protection._is_metadata_endpoint("metadata.google.internal") is True
    assert protection._is_metadata_endpoint("notmetadata.google.internal.example") is False


def test_domain_allowlist_requires_label_boundary(protection):
    protection.settings.allowed_domains = ["example.com"]
    assert protection._is_domain_allowed("agent.example.com") is True
    assert protection._is_domain_allowed("notexample.com") is False
