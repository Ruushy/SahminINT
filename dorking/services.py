import json
import urllib.parse
from django.urls import reverse


def url_encode(query):
    return urllib.parse.quote(query, safe="")


def build_search_urls(query, domain):
    q = query.format(domain=domain)
    encoded = url_encode(q)
    return {
        "query": q,
        "google": f"https://www.google.com/search?q={encoded}",
        "bing": f"https://www.bing.com/search?q={encoded}",
        "duckduckgo": f"https://duckduckgo.com/?q={encoded}",
    }


def build_github_url(query, domain):
    q = query.format(domain=domain)
    encoded = url_encode(q)
    return {
        "query": q,
        "github": f"https://github.com/search?q={encoded}&type=code",
    }
