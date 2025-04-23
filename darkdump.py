# Darkdump v3 - Safe JSON Export Version for Dark Web Analysis
__version__ = 3

import sys
sys.dont_write_bytecode = True  # Prevents creation of .pyc files

# Required libraries
import requests
from bs4 import BeautifulSoup
import os
import argparse
import random
import re
import json
from headers.agents import Headers  # Custom header pool

# NLP tools
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from textblob import TextBlob

# Info banner
notice = '''
Note: 
    This tool is not to be used for illegal purposes.
    The author is not responsible for any misuse of Darkdump.
    May God bless you all.
    https://joshschiavone.com - https://github.com/josh0xA
'''

# ANSI color formatting for terminal output
class Colors:
    W = '\033[0m'
    R = '\033[31m'
    G = '\033[32m'
    O = '\033[33m'
    B = '\033[34m'
    P = '\033[35m'
    C = '\033[36m'
    GR = '\033[37m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Global configuration settings
class Configuration:
    __darkdump_api__ = "https://ahmia.fi/search/?q="  # Ahmia search endpoint
    __socks5init__ = "socks5h://localhost:9050"        # Tor proxy config

# Handles platform-specific tasks
class Platform:
    def __init__(self, execpltf):
        self.execpltf = execpltf

    # Displays the detected OS
    def get_operating_system_descriptor(self):
        if self.execpltf:
            print(f"{Colors.BOLD}{Colors.W}Operating System: {Colors.G}{sys.platform}{Colors.END}")

    # Clears screen depending on OS
    def clean_screen(self):
        if self.execpltf:
            os.system('cls' if os.name == 'nt' else 'clear')

    # Verifies Tor is running via IP check
    def check_tor_connection(self, proxy_config):
        try:
            r = requests.get('http://api.ipify.org', proxies=proxy_config, timeout=10)
            print(f"{Colors.BOLD + Colors.G}Tor service is active. IP: {r.text}{Colors.END}")
            return True
        except:
            print(f"{Colors.BOLD + Colors.R} Tor is inactive. Cannot scrape.{Colors.END}")
            return False

# Main logic class for Darkdump
class Darkdump:
    # Removes HTML tags and normalizes spacing
    def clean_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        text = re.sub(r'[\r\n]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return re.sub(r'[^a-zA-Z0-9\s]', '', text).strip()

    # Extracts top keywords from the text content
    def extract_keywords(self, text):
        words = word_tokenize(self.clean_text(text).lower())
        stop_words = set(stopwords.words('english'))
        filtered = [w for w in words if w.isalnum() and w not in stop_words]
        return list(FreqDist(filtered))[:18]

    # Performs sentiment analysis and keyword frequency analysis
    def analyze_text(self, text):
        words = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        filtered = [w for w in words if w.lower() not in stop_words and w.isalnum()]
        freq = FreqDist(filtered)
        blob = TextBlob(text)
        return {
            'top_words': freq.most_common(10),
            'sentiment': {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        }

    # Collects meta tags from the HTML
    def extract_metadata(self, soup):
        return {meta.get('name') or meta.get('property'): meta.get('content')
                for meta in soup.find_all('meta') if meta.get('name') or meta.get('property')}

    # Extracts all hyperlinks from the page
    def extract_links(self, soup):
        return [a['href'] for a in soup.find_all('a', href=True)]

    # Finds all email patterns in the HTML text
    def extract_emails(self, soup):
        return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.get_text())

    # Finds file links that end with specified document extensions
    def extract_documents(self, soup):
        extensions = ['.pdf', '.docx', '.txt', '.xlsx', '.csv', '.json', '.zip']
        return [a['href'] for a in soup.find_all('a', href=True) if any(a['href'].endswith(ext) for ext in extensions)]

    # Main scraping method
    def crawl(self, query, amount, use_proxy=False, scrape_sites=False):
        headers = {'User-Agent': random.choice(Headers.user_agents)}
        proxy = {'http': Configuration.__socks5init__, 'https': Configuration.__socks5init__} if use_proxy else {}

        # Normalize query to safe filename
        safe_query = re.sub(r'[^a-zA-Z0-9_\-]', '_', query.strip().lower())
        output_file = f'./results/darkdump_output_{safe_query}.json'
        clean_file = f'./results/clean_{safe_query}.json'

        # Start Ahmia search
        try:
            r = requests.get(Configuration.__darkdump_api__ + query, headers=headers)
            soup = BeautifulSoup(r.content, 'html.parser')
            results = soup.find(id='ahmiaResultsPage')

            # Handle site structure error
            if not results:
                print(f"{Colors.BOLD + Colors.R}[!] Ahmia structure changed. No results section.{Colors.END}")
                fallback = [{
                    "query": query,
                    "status": "ahmia_structure_error",
                    "message": "Ahmia layout changed. Cannot parse results.",
                    "results": []
                }]
                with open(output_file, 'w') as f: json.dump(fallback, f, indent=2)
                with open(clean_file, 'w') as f: json.dump(fallback, f, indent=2)
                print(f"{Colors.BOLD + Colors.C}[~] Layout error written to {output_file} and {clean_file}{Colors.END}")
                return

            items = results.find_all('li', class_='result')
            if not items:
                print(f"{Colors.BOLD + Colors.O}[!] No results for query: {query}{Colors.END}")
                no_data = [{
                    "query": query,
                    "status": "no_results",
                    "message": f"No dark web entries found for the given keyword: {query}",
                    "results": []
                }]
                with open(output_file, 'w') as f: json.dump(no_data, f, indent=2)
                with open(clean_file, 'w') as f: json.dump(no_data, f, indent=2)
                print(f"{Colors.BOLD + Colors.C}[~] Empty results written to {output_file} and {clean_file}{Colors.END}")
                return
        except Exception as e:
            print(f"{Colors.BOLD + Colors.R} Ahmia fetch error: {e}{Colors.END}")
            return

        seen, data = set(), []

        # Confirm Tor is working if scraping content
        if scrape_sites and not Platform(True).check_tor_connection(proxy):
            return

        # Process each result
        for i, item in enumerate(items[:amount]):
            url = item.find('cite').text.strip()
            if not url.startswith('http'):
                url = 'http://' + url
            if url in seen:
                continue
            seen.add(url)

            title = item.find('a').text.strip() if item.find('a') else 'N/A'
            description = item.find('p').text.strip() if item.find('p') else 'N/A'

            entry = {'title': title, 'description': description, 'url': url}

            if scrape_sites:
                try:
                    r = requests.get(url, headers=headers, proxies=proxy, timeout=10)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    entry['metadata'] = self.extract_metadata(soup)
                    entry['keywords'] = self.extract_keywords(soup.get_text())
                    entry['sentiment'] = self.analyze_text(soup.get_text())['sentiment']
                    entry['emails'] = self.extract_emails(soup)
                    entry['documents'] = self.extract_documents(soup)
                    entry['links'] = self.extract_links(soup)
                except:
                    entry['error'] = 'Unreachable or Tor blocked'

            data.append(entry)

        # Write raw output
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"{Colors.BOLD + Colors.C}[*] Results written to {output_file}{Colors.END}")

        # Write cleaned summary for dashboard/db
        cleaned_data = []
        for entry in data:
            alert_flag = "\u26a0\ufe0f Possible Data Exposure" if entry.get('emails') or entry.get('documents') else "\u2705 No Risk"
            cleaned_data.append({
                "title": entry.get("title", "N/A"),
                "url": entry.get("url", "N/A"),
                "summary": entry.get("description", "N/A"),
                "top_keywords": entry.get("keywords", [])[:10],
                "emails_found": entry.get("emails", []),
                "documents_found": entry.get("documents", []),
                "link_count": len(entry.get("links", [])),
                "sentiment": entry.get("sentiment", {}),
                "alert": alert_flag
            })

        with open(clean_file, 'w') as f:
            json.dump(cleaned_data, f, indent=2)
        print(f"{Colors.BOLD + Colors.G}[+] Clean summary written to {clean_file}{Colors.END}")

# CLI argument handler and entry point
def darkdump_main():
    Platform(True).clean_screen()
    Platform(True).get_operating_system_descriptor()
    print(notice)

    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', type=str, help='Query to search')
    parser.add_argument('-a', '--amount', type=int, default=10)
    parser.add_argument('-p', '--proxy', action='store_true')
    parser.add_argument('-s', '--scrape', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    args = parser.parse_args()

    if args.version:
        print(f"Darkdump Version: {__version__}")
        return
    if not args.query:
        print("[!] Missing -q <query>")
        return

    print(f"[+] Searching for '{args.query}' with limit {args.amount}")
    Darkdump().crawl(query=args.query, amount=args.amount, use_proxy=args.proxy, scrape_sites=args.scrape)

if __name__ == '__main__':
    darkdump_main()
