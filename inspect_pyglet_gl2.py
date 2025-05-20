import pyglet.gl as gl
print('pyglet.gl attributes:')
print([attr for attr in dir(gl)])
if hasattr(gl, '_lib'):
    print('pyglet.gl._lib attributes:')
    print([attr for attr in dir(gl._lib)])



from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import csv
import re


class WikiScraper:
    def __init__(self, driver_path):
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)

    def clean_text(self, text, name):
        text = re.sub(r'\[\w+]', '', text)
        text = re.sub(re.escape(name), '', text, flags=re.IGNORECASE)
        text = re.sub(r'(Tamil|Telugu|Hindi|Malayalam|Kannada|Bengali)(,\1)+', r'\1', text, flags=re.IGNORECASE)
        words = text.split()
        deduped = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() != words[i - 1].lower():
                deduped.append(word)
        text = ' '.join(deduped)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r',\s*,+', ',', text)
        return text.strip(' ,')



    def extract_paragraphs(self, soup, url, title):
        paragraphs = []
        if "wikipedia.org" in url:
            content_div = soup.find("div", {"class": "vector-body ve-init-mw-desktopArticleTarget-targetContainer"})
        else:
            content_div = soup.find("article") or soup.find("div", class_=re.compile("content|article|story", re.I))

        if content_div:
            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    text = self.clean_text(text, title)
                    paragraphs.append(text)
        return " ".join(paragraphs[:3])

    def scrape_page(self, url):
        self.driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        data = {}

        try:
            title_tag = soup.find("h1")
            title = title_tag.text.strip() if title_tag else "N/A"
        except:
            title = "N/A"
        data["title"] = title

        try:
            paragraph = self.extract_paragraphs(soup, url, title)
        except Exception as e:
            paragraph = f"Error: {e}"
        data["paragraph"] = paragraph

        if "wikipedia.org" in url:
            infobox = soup.find("table", {"class": "infobox biography vcard"})
            if infobox:
                rows = infobox.find_all("tr")
                for row in rows:
                    header = row.find("th")
                    value = row.find("td")
                    if header and value:
                        label = header.text.strip().lower()
                        content = value.text.strip().replace("\n", " ")
                        if label == "born" and content in paragraph:
                            continue
                        data[label] = self.clean_text(content, title)

        data["url"] = url
        return data

    def scrape_multiple(self, urls):
        all_data = []
        for url in urls:
            page_data = self.scrape_page(url)
            for key, value in page_data.items():
                all_data.append({"Key": key, "Value": value})
            all_data.append({"Key": "", "Value": ""})
        return all_data

    def format_data_as_string(self, all_data):
        output = []
        for row in all_data:
            if row["Key"] == "" and row["Value"] == "":
                output.append("\n" + "="*50 + "\n")
            else:
                output.append(f"{row['Key'].capitalize()}: {row['Value']}")
        return "\n".join(output)

    def save_to_csv(self, all_data, filename="wiki_output_clean.csv"):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Key", "Value"])
            writer.writeheader()
            for row in all_data:
                writer.writerow(row)

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    urls = [
        "https://en.wikipedia.org/wiki/Rajinikanth",
        "https://www.hindustantimes.com/entertainment/tamil-cinema/rajinikanth-says-indian-youth-are-immersed-in-western-culture-while-westerners-find-peace-in-meditation-101746015191480.html",
    ]

    scraper = WikiScraper(driver_path=r"D:\helloworld\chromedriver-win64\chromedriver.exe")
    all_data = scraper.scrape_multiple(urls)

    scraper.save_to_csv(all_data)

    formatted_output = scraper.format_data_as_string(all_data)
    print("✅ Data cleaned and saved in key-value format.\n")
    print(formatted_output)

    scraper.close()