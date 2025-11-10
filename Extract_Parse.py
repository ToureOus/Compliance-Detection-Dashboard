import xml.etree.ElementTree as ET
import pandas as pd
import re
import requests
from datetime import datetime


def fetch_and_save_xml(url, file_name):
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Succesfully connected to {url}")
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(response.content.decode('utf-8'))
        print(f"ECFR XML Data saved to {file_name}")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        print("Response content:", response.text)


def parse_xml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    root = ET.fromstring(file_content)

    data = []
    current_country = None

    for tr in root.iter('TR'):
        tds = tr.findall('TD')
        if len(tds) > 0 and 'scope' in tds[0].attrib and tds[0].text and tds[0].text.strip():
            current_country = tds[0].text.strip()
        elif current_country and len(tds) > 1:
            entity_info, license_requirement, license_review_policy, federal_register_citation = extract_information(
                tds)
            data.append({
                'Country': current_country,
                'Entity Info': entity_info,
                'License Requirement': license_requirement,
                'License Review Policy': license_review_policy,
                'Federal Register Citation': federal_register_citation
            })

    return data


def write_data_to_csv(data, output_file):
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"CSV Data saved to {output_file}")


def get_latest_update_date():
    response = requests.get("https://www.ecfr.gov/api/versioner/v1/versions.json")
    if response.status_code == 200:
        data = response.json()
        for item in data["title_versions"]:
            if item["title"] == 15:
                return item["last_updated"]
    return None


def clean_html(html_content):
    clean_text = re.sub('<[^<]+?>', '', html_content)
    clean_text = clean_text.replace('â', '-').replace('\n', ' ').replace('\r', ' ')
    return clean_text.strip()


def extract_information(td_elements):
    cleaned_elements = [clean_html(ET.tostring(td, encoding='unicode')) for td in td_elements]
    entity_info = cleaned_elements[1] if len(cleaned_elements) > 1 else ''
    license_requirement = cleaned_elements[2] if len(cleaned_elements) > 2 else ''
    license_review_policy = cleaned_elements[3] if len(cleaned_elements) > 3 else ''
    federal_register_citation = cleaned_elements[4] if len(cleaned_elements) > 4 else ''
    return entity_info, license_requirement, license_review_policy, federal_register_citation


def main():
    title_15_update = get_latest_update_date()
    if title_15_update:
        url = f"https://www.ecfr.gov/api/versioner/v1/full/{title_15_update}/title-15.xml?appendix=Supplement+No.+4+to+Part+744&part=744"
        xml_file_name = 'ecfr_title_15_part_744.xml'
        fetch_and_save_xml(url, xml_file_name)
        extracted_data = parse_xml(xml_file_name)
        current_date = datetime.now().strftime("%Y-%m-%d")
        # output_csv = f'ecfr_title_15_part_744_extracted_{current_date}.csv'
        output_csv = f'ecfr_title_15_part_744_extracted.csv'

        write_data_to_csv(extracted_data, output_csv)
    else:
        print("Updated date for Title 15 not found")


if __name__ == "__main__":
    main()