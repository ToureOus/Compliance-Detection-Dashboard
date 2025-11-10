import requests
import os
import zipfile
import datetime
import shutil

# GitHub API URL for the releases of cvelistV5
releases_api_url = 'https://api.github.com/repos/CVEProject/cvelistV5/releases'

# Directory to store extracted CVE data
extract_dir = 'cve_data/cvelistV5'


def yesterday_delta_files():
    # Calculate yesterday's date
    yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    yesterday_date = yesterday.strftime('%Y-%m-%d')

    # Construct the target string for "at end of day" delta release
    target_string = f"{yesterday_date}_at_end_of_day"
    print(f"Looking for 'at end of day' delta update for: {yesterday_date}")

    response = requests.get(releases_api_url)
    if response.status_code == 200:
        releases = response.json()
        for release in releases:
            # Check if the 'tag_name' matches our target string
            if target_string in release['tag_name']:
                print(f"Matching 'at end of day' release found: {release['tag_name']}")
                # Assume direct download URL follows this pattern
                direct_dl = f"https://github.com/CVEProject/cvelistV5/releases/download/{release['tag_name']}/{yesterday_date}_delta_CVEs_at_end_of_day.zip"
                return direct_dl
    else:
        print(f"Failed to fetch releases, status code: {response.status_code}")
        return None


def append_files(delta_dir, target_base_dir):
    """
    Move files from the delta directory to their corresponding locations in the
    original file structure, overwriting existing files if necessary.
    """
    for root, dirs, files in os.walk(delta_dir):
        for file in files:
            if file.endswith(".json") and file.startswith("CVE-"):
                # Extract the year and ID for constructing the target path
                parts = file.split("-")
                year = parts[1]
                cve_number = parts[2].split(".")[0]  # Assuming format is CVE-YEAR-NUMBER.json

                # Determine folder based on the length of the CVE number
                if len(cve_number) == 5:
                    target_subdir = os.path.join(target_base_dir, "cves", year, cve_number[:2] + "xxx")
                elif len(cve_number) == 4:
                    target_subdir = os.path.join(target_base_dir, "cves", year, cve_number[0] + "xxx")
                else:
                    print(f"Unexpected CVE number length in {file}, skipping.")
                    continue

                if not os.path.exists(target_subdir):
                    os.makedirs(target_subdir)

                target_file_path = os.path.join(target_subdir, file)
                shutil.move(os.path.join(root, file), target_file_path)
                print(f"Moved {file} to {target_file_path}")


def Download_fullCVE():
    """
    Downloads the full CVE archive for yesterday at midnight, extracts it,
    and then extracts the nested 'cves.zip' file if present.
    """
    yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    yesterday_date = yesterday.strftime('%Y-%m-%d')
    full_archive_url = f"https://github.com/CVEProject/cvelistV5/releases/download/cve_{yesterday_date}_2300Z/{yesterday_date}_all_CVEs_at_midnight.zip.zip"

    zip_file_path = os.path.join(extract_dir, f"{yesterday_date}_all_CVEs_at_midnight.zip.zip")

    print(f"Downloading full CVE archive from {full_archive_url}...")
    response = requests.get(full_archive_url, stream=True)

    if response.status_code == 200:
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
        with open(zip_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        print("Full CVE archive download complete.")

        print("Extracting the full CVE archive...")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print("Extraction complete.")

        # Locate and extract the nested 'cves.zip' if it exists
        nested_zip_path = os.path.join(extract_dir, 'cves.zip')
        if os.path.exists(nested_zip_path):
            print("Extracting the nested 'cves.zip'...")
            with zipfile.ZipFile(nested_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print("'cves.zip' extraction complete.")

            # Optional: Cleanup the 'cves.zip' file after extraction
            os.remove(nested_zip_path)
            print(f"Removed nested archive '{nested_zip_path}'.")

        # Optional: Cleanup the downloaded ZIP file after all extractions
        os.remove(zip_file_path)
        print(f"Removed downloaded archive '{zip_file_path}'.")
    else:
        print(f"Failed to download the full CVE archive, status code: {response.status_code}")


def main():
    zip_url = yesterday_delta_files()
    yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    yesterday_date = yesterday.strftime('%Y-%m-%d')
    if zip_url:
        zip_file_path = os.path.join(extract_dir, f'{yesterday_date}_end_of_day_delta_cve_data.zip')

        print(f"Downloading CVE delta data from {zip_url}...")
        response = requests.get(zip_url, stream=True)
        if response.status_code == 200:
            with open(zip_file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
            print("Download complete.")

            # Define delta extraction directory
            delta_extract_dir = os.path.join(extract_dir, "deltaCves")
            if not os.path.exists(delta_extract_dir):
                os.makedirs(delta_extract_dir)

            print("Extracting the ZIP file...")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(delta_extract_dir)
            print("Extraction complete.")

            print("Moving delta files to their respective directories...")
            append_files(delta_extract_dir, extract_dir)
            print("Delta files moved successfully.")

            # Cleanup
            os.remove(zip_file_path)
            shutil.rmtree(delta_extract_dir)
            print(f"Cleanup complete. Removed {zip_file_path} and deltaCves directory.")
        else:
            print(f"Failed to download the file, status code: {response.status_code}")
    else:
        print("No 'at end of day' delta release found for yesterday.")
    # Download_fullCVE() uncomment to download full archive

if __name__ == "__main__":
    main()