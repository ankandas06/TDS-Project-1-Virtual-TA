from playwright.sync_api import sync_playwright
import json
import time
from bs4 import BeautifulSoup

BASE_URL = "https://tds.s-anand.net"

def get_cleaned_course_content(out_dir):
    cleaned_content = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        scrap_url = f"{BASE_URL}/#/2025-01/"
        print(scrap_url)
        page.goto(scrap_url)
        page.wait_for_selector(".sidebar-nav .folder a", timeout=10000)
        sidebar_links = page.query_selector_all(".sidebar-nav .folder a")
        for link_handle in sidebar_links:
            link = link_handle.get_attribute('href')
            title = link_handle.inner_text()
            inner_page_url = f"{BASE_URL}/{link}"
            print(inner_page_url)
            page.goto(inner_page_url)
            
            page.wait_for_selector(".sidebar-nav .folder a", timeout=10000)
            page.wait_for_selector("#main", timeout=10000)
            main_content = page.query_selector("#main")
            raw_html = main_content.inner_html()
            soup = BeautifulSoup(raw_html, "html.parser")
            parts = []
            for tag in soup.find_all(["h1","h2","h3","p","li","ui","pre","code"]):
                text = tag.get_text(strip=True)
                if text:
                    parts.append(text)
            
            full_text = f"{title}\n"+"\n".join(parts)
            cleaned_content.append({
                "title":title,
                "url":inner_page_url,
                "text":full_text
            })
            with open(out_dir,"w") as f:
                json.dump(cleaned_content, f, indent=2)
    return cleaned_content

if __name__ == "__main__":
    get_cleaned_course_content("cleaned_course.json")
    
        
    


