import requests
from bs4 import BeautifulSoup

url = "https://cybernews.com/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('link', type='application/rss+xml')
for link in links:
    print(f"RSS Link: {link.get('href')}")

links = soup.find_all('a')
for link in links:
    if 'rss' in link.get('href', '').lower() or 'feed' in link.get('href', '').lower():
         print(f"Potential Feed Link: {link.get('href')}")
