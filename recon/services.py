import re
import ssl
import socket
import logging
import requests
import urllib3
import dns.resolver
from datetime import datetime, timezone
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cryptography import x509
from cryptography.x509.oid import NameOID

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}
HTTP_TIMEOUT = 20

_session = None


def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        retry_strat = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strat, pool_connections=20, pool_maxsize=40)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
        _session.headers.update(HEADERS)
        _session.verify = False
    return _session


def _fetch_json(url, timeout=15):
    try:
        resp = _get_session().get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.debug("JSON fetch failed: %s - %s", url, e)
    return None


def _fetch_text(url, timeout=15):
    try:
        resp = _get_session().get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        logger.debug("Text fetch failed: %s - %s", url, e)
    return None


def _extract_hostnames(text):
    if not text:
        return set()
    return set(re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', text))


def _clean_host(h):
    h = h.strip().lower()
    if h.startswith("."):
        h = h[1:]
    if h.startswith("*."):
        h = h[2:]
    return h


# ── Subdomain Enumeration ──────────────────────────────────────────

def enumerate_subdomains(domain):
    results = {}
    seen = set()
    domain = domain.lower().strip()
    dot_domain = "." + domain

    def add(host, source):
        host = _clean_host(host)
        if not host or host == domain:
            return
        if not host.endswith(dot_domain):
            return
        if host not in seen:
            seen.add(host)
            results.setdefault(host, []).append(source)

    # 1. crt.sh
    try:
        data = _fetch_json(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20)
        if data:
            for entry in data:
                name = entry.get("name_value", "")
                for h in name.split("\n"):
                    add(h, "crt.sh")
    except Exception as e:
        logger.debug("crt.sh error: %s", e)

    # 2. AlienVault OTX
    try:
        data = _fetch_json(f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", timeout=15)
        if data:
            for entry in data.get("passive_dns", []):
                add(entry.get("hostname") or "", "alienvault")
    except Exception as e:
        logger.debug("AlienVault error: %s", e)

    # 3. HackerTarget
    try:
        text = _fetch_text(f"https://api.hackertarget.com/hostsearch/?q={domain}", timeout=15)
        if text:
            for line in text.strip().split("\n"):
                parts = line.split(",")
                if parts:
                    add(parts[0], "hackertarget")
    except Exception as e:
        logger.debug("HackerTarget error: %s", e)

    # 4. RapidDNS
    try:
        text = _fetch_text(f"https://rapiddns.io/subdomain/{domain}", timeout=15)
        if text:
            for h in _extract_hostnames(text):
                add(h, "rapiddns")
    except Exception as e:
        logger.debug("RapidDNS error: %s", e)

    # 5. BufferOver
    try:
        data = _fetch_json(f"https://dns.bufferover.run/dns/v1/reverse/.{domain}", timeout=15)
        if data:
            for entry in data.get("FDNS_A", []):
                parts = entry.split(",")
                if len(parts) >= 2:
                    add(parts[1], "bufferover")
            for entry in data.get("RDNS", []):
                parts = entry.split(",")
                if len(parts) >= 2:
                    add(parts[1], "bufferover")
    except Exception as e:
        logger.debug("BufferOver error: %s", e)

    # 6. Wayback CDX
    try:
        text = _fetch_text(
            f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=text&fl=original&collapse=urlkey&limit=10000",
            timeout=25,
        )
        if text:
            for line in text.strip().split("\n"):
                try:
                    parsed = urlparse(line.strip())
                    add(parsed.hostname or "", "wayback")
                except Exception:
                    pass
    except Exception as e:
        logger.debug("Wayback CDX error: %s", e)

    # 7. CertSpotter (SSLMate)
    try:
        data = _fetch_json(f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names", timeout=15)
        if data:
            for entry in data:
                for dns_name in entry.get("dns_names", []):
                    add(dns_name, "certspotter")
    except Exception as e:
        logger.debug("CertSpotter error: %s", e)

    # 8. URLScan.io
    try:
        data = _fetch_json(
            f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=100",
            timeout=15,
        )
        if data:
            for result in data.get("results", []):
                page = result.get("page", {})
                add(page.get("domain", ""), "urlscan")
    except Exception as e:
        logger.debug("URLScan error: %s", e)

    return results


# ── DNS Records ────────────────────────────────────────────────────

def query_dns(domain):
    results = []
    types = [
        ("A", "A"),
        ("AAAA", "AAAA"),
        ("MX", "MX"),
        ("TXT", "TXT"),
        ("NS", "NS"),
        ("CNAME", "CNAME"),
        ("SOA", "SOA"),
        ("SRV", "SRV"),
        ("CAA", "CAA"),
    ]
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 10

    for rt, label in types:
        try:
            answers = resolver.resolve(domain, rt, raise_on_no_answer=False)
            if answers.rrset is None:
                continue
            for rdata in answers:
                val = str(rdata).replace("\n", " ")[:600]
                ttl = answers.rrset.ttl if answers.rrset else None
                results.append({
                    "record_type": label,
                    "value": val,
                    "ttl": ttl,
                })
        except dns.resolver.NXDOMAIN:
            break
        except dns.exception.Timeout:
            logger.debug("DNS %s timeout for %s", rt, domain)
            continue
        except Exception as e:
            logger.debug("DNS %s error for %s: %s", rt, domain, e)
            continue

    return results


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


# ── SSL / TLS Certificate Check ────────────────────────────────────

COMMON_SSL_PORTS = [443, 8443, 465, 993, 995, 2525, 587]


def _parse_cryptography_cert(der_data):
    try:
        cert = x509.load_der_x509_certificate(der_data)
        cn = ""
        org = ""
        try:
            cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        except Exception:
            pass
        try:
            org = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
        except Exception:
            pass
        issuer_cn = ""
        try:
            issuer_cn = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        except Exception:
            pass

        san_list = []
        try:
            ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            san_list = ext.value.get_values_for_type(x509.DNSName)
        except Exception:
            pass

        if hasattr(cert, "not_valid_before_utc"):
            not_before = cert.not_valid_before_utc.isoformat()
            not_after = cert.not_valid_after_utc.isoformat()
            expires = not_after
            remaining_days = (cert.not_valid_after_utc - datetime.now(timezone.utc)).days
        else:
            not_before = cert.not_valid_before.isoformat()
            not_after = cert.not_valid_after.isoformat()
            expires = not_after
            expiry = cert.not_valid_after.replace(tzinfo=timezone.utc)
            remaining_days = (expiry - datetime.now(timezone.utc)).days

        serial = str(cert.serial_number)[:100]
        sig_algo = cert.signature_algorithm_oid._name if hasattr(cert.signature_algorithm_oid, "_name") else str(cert.signature_algorithm_oid)

        return {
            "subject_cn": cn,
            "issuer_cn": issuer_cn,
            "org": org,
            "san": ", ".join(san_list[:20]),
            "not_before": not_before,
            "not_after": not_after,
            "expires": expires,
            "remaining_days": remaining_days,
            "serial": serial,
            "version": cert.version.value if hasattr(cert.version, "value") else str(cert.version),
            "signature_algorithm": sig_algo,
        }
    except Exception as e:
        logger.debug("Cryptography cert parse error: %s", e)
        return None


def check_ssl(domain):
    results = []
    for port in COMMON_SSL_PORTS:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.options |= ssl.OP_NO_SSLv2
            ctx.options |= ssl.OP_NO_SSLv3
            with socket.create_connection((domain, port), timeout=8) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    der_data = ssock.getpeercert(binary_form=True)
                    if not der_data:
                        cert = ssock.getpeercert(binary_form=False)
                        if not cert:
                            continue
                        parsed = None
                    else:
                        parsed = _parse_cryptography_cert(der_data)
                    if parsed is None:
                        continue
                    parsed["port"] = port
                    results.append(parsed)
        except (ssl.SSLError, ConnectionRefusedError, socket.timeout, OSError) as e:
            logger.debug("SSL check %s:%d - %s", domain, port, e)
            continue

    return results


# ── Email Harvesting ───────────────────────────────────────────────

HARVEST_PATHS = [
    "/", "/contact", "/about", "/about-us", "/team", "/support",
    "/privacy", "/privacy-policy", "/terms", "/contact-us", "/company",
    "/careers", "/join-us", "/staff", "/directory",
]

HARVEST_ROBOTS_PATH = "/robots.txt"
HARVEST_SITEMAP_PATHS = ["/sitemap.xml", "/sitemap_index.xml"]


def _scrape_page_for_emails(url, domain, timeout=15):
    try:
        text = _fetch_text(url, timeout=timeout)
        if not text:
            return set()
        found = set(EMAIL_RE.findall(text))
        result = set()
        for e in found:
            el = e.lower()
            if el.endswith("@" + domain.lower()) or el.endswith("." + domain.lower()):
                result.add(el)
        return result
    except Exception:
        return set()


def harvest_emails(domain):
    emails = set()
    domain = domain.lower().strip()

    for path in HARVEST_PATHS:
        for scheme in ("https", "http"):
            url = f"{scheme}://{domain}{path}"
            found = _scrape_page_for_emails(url, domain)
            if found:
                emails.update(found)
                break

    for spath in HARVEST_SITEMAP_PATHS:
        url = f"https://{domain}{spath}"
        text = _fetch_text(url, timeout=10)
        if text:
            for url_match in re.findall(r'<loc>(.*?)</loc>', text, re.I):
                found = _scrape_page_for_emails(url_match, domain, timeout=10)
                emails.update(found)

    return sorted(emails)
