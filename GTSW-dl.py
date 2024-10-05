import os
import shutil
import sys
import time
import re
import csv
import datetime
import unidecode
import PyPDF2

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ChunkedEncodingError
import pdfkit

DLMODE = 0 # 0 is Save to Disk / 1 is CSV Export

path_wkhtmltopdf = r'.\wkhtmltopdf.exe'
imageOptions={'no-images': None}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# Load the cookies from the Netscape HTTP Cookie File
def parseCookieFile(cookiefile):

    cookies = {}
    with open(cookiefile, "r") as fp:
        for line in fp:
            if not re.match(r"^\#", line):
                lineFields = re.findall(
                    r"[^\s]+", line
                )  # capturing anything but empty space
                try:
                    cookies[lineFields[5]] = lineFields[6]
                except Exception as e:
                    print(e)

    return cookies

# Define a function to make the request with retries
def make_request_with_retries(url, cookies, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, cookies=cookies, timeout=30)
            response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
            return response
        except (ChunkedEncodingError, requests.exceptions.RequestException) as e:
            print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)  # Add a 5-second delay before retrying
    print("Max retries reached, skipping the request.")
    return None

def uidToAuth(uid):
    # Construct the URL with the provided uid
    url = f"https://www.[REDACTED].net/viewuser.php?action=storiesby&uid={uid}"

    # Send an HTTP request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the span with class "label" containing "Penname: "
        penname_span = soup.find("span", {"class": "label"}, string="Penname: ")

        # Check if the penname_span is found
        if penname_span:
            # Extract the following text as the author name
            next_text = penname_span.find_next_sibling(string=True)
            # Extract the author name and remove unnecessary characters
            author_name = next_text.strip().split("[")[0].strip()
            return author_name
        else:
            return None  # Penname span not found
    else:
        return None  # Request was not successful
    
def extract_word_count(pdf_path, num_pages=5):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract text from the first 'num_pages' pages
        text = ""
        for page_num in range(min(num_pages, len(pdf_reader.pages))):
            text += pdf_reader.pages[page_num].extract_text()

        # Search for "Word count:" in the concatenated text
        word_count_index = text.find("Word count:")
        if word_count_index != -1:
            word_count_str = text[word_count_index + len("Word count:"):].split()[0]
            return int(word_count_str)
        else:
            return None
        
# Function to extract file size from a file
def extract_file_size(filepath):
    return os.path.getsize(filepath)
    
def downloadStories(action=None, uid=None, storylist=None, downloads_dir=None):

    # Check for required arguments
    if action is None:
        raise ValueError("The 'action' argument is required.")
    if action == "list" and storylist is None:
        raise ValueError("For 'list' action, the 'storylist' argument is required.")
    if action != "list" and uid is None:
        raise ValueError("For actions other than 'list', the 'uid' argument is required.")
    if downloads_dir == None:
        raise ValueError("Download directory is always required.")
    
    # Initialize the arrays to store the stories
    story_titles = []
    story_authors = []
    story_links = []
    story_ids = []

    if action != "file":

        # Loop through the pages and extract the stories
        current_num = 0

        # Set the URL template of the restricted webpage with a placeholder for the offset parameter
        base_url = f"https://www.[REDACTED].net/viewuser.php?action={action}&uid={uid}&offset="
        # print(base_url)

        while True:

            # Set the URL of the current page
            url = base_url + str(current_num * 20)

            # Send a GET request to the current page with the cookies
            response = make_request_with_retries(url, cookies)

            # Check if the access was successful by searching for the error message
            if "You are not authorized to access that function." in response.text:
                print(f"Access to page {current_num + 1} on user {uid}'s {action} page was unsuccessful.")
                break

            # Parse the HTML content of the response using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all the story links on the page and add them to the story_links array
            for div in soup.find_all("div", class_="title"):
                # Extract the title, author, and link of the story
                story_title = div.find("span", class_="story-title").text.strip()
                story_author = div.find(
                    "span", class_="story-title"
                ).next_sibling.next_sibling.text.strip()
                story_link = div.find("a")["href"]
                # Extract only the integer part of the story link
                story_id = int(story_link.split("=")[-1])

                # Append the title, author, and link to their respective arrays
                story_titles.append(story_title)
                story_authors.append(story_author)
                story_links.append(story_link)
                story_ids.append(story_id)

            # Check if there are more pages by looking for the "next" button
            next_button = soup.find("a", string="[Next]")
            if not next_button:
                break

            # Increment the page number to go to the next page
            current_num += 1

    if action == "list":

        story_ids = storylist      

    # Print the number of stories found
    match action:
        case "favst":
            print(f"\nUser {uidToAuth(uid)} has {len(story_titles)} favourite stories.")

        case "storiesby":
            print(f"\nAuthor {uidToAuth(uid)} has made {len(story_ids)} stories.")

        case "list":
            print(f"\nThere are {len(story_ids)} stories in this list.")

    # print(f"Found {len(story_authors)} authors.")
    # print(f"Found {len(story_links)} links.")
    # print(f"Found {len(story_ids)} IDs.")

    # # Print the list of story titles
    # print("Story titles:")
    # print(story_titles)

    # # Print the list of story authors
    # print("Story authors:")
    # print(story_authors)

    # # Print the list of story links
    # print("Story links:")
    # print(story_links)

    # # Print the list of story ids
    # print("Story IDs:")
    # print(story_ids)
            
    if DLMODE == 1:

        # Construct the CSV file path
        script_directory = os.path.dirname(os.path.abspath(__file__))
        csv_directory = os.path.join(script_directory, "CSV Link Exports")

        # Create the "CSV Link Exports" folder if it doesn't exist
        if not os.path.exists(csv_directory):
            os.makedirs(csv_directory)

        current_date = datetime.date.today()
        csv_filepath = os.path.join(csv_directory, f"Story Link Exports [{current_date}].csv")

        # Open the CSV file for writing
        with open(csv_filepath, mode='a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)

            # Write user/author page
            csv_writer.writerow([f"https://www.[REDACTED].net/viewuser.php?action=favau&uid={uid}"])

            # Loop through each story ID and save the printable version as a PDF
            for i, story_id in enumerate(story_ids):
                # Construct the URL of the printable version of the story
                printable_url = f"https://www.[REDACTED].net/viewstory.php?action=printable&sid={story_id}&textsize=0&chapter=all"

                # Write the printable URL to the CSV file
                csv_writer.writerow([printable_url])

                
    if DLMODE == 0:
        # Loop through each story ID and save the printable version as a PDF
        for i, story_id in enumerate(story_ids):
            # Construct the URL of the printable version of the story
            printable_url = f"https://www.[REDACTED].net/viewstory.php?action=printable&sid={story_id}&textsize=0&chapter=all"

            # Send a GET request to the printable URL with the cookies
            response = make_request_with_retries(printable_url, cookies)
            if response is None:
                continue 

            # Parse the HTML content of the response using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract the story title and author from the page title
            page_title = soup.find("title").text.strip()
            page_title_parts = page_title.split(" by ")
            story_title = page_title_parts[0]
            story_author = page_title_parts[1]

            # Define illegal characters
            illegal_chars = "#%&{}\\<>*?/$!'\"@+`|=:"

            # Add non-ASCII characters to the list of illegal characters
            non_ascii_chars = "".join(chr(i) for i in range(128, 256))
            illegal_chars += non_ascii_chars

            # Function to remove diacritics and convert special characters
            def clean_and_convert(text):
                cleaned_text = unidecode.unidecode(text)
                return "".join(c if c not in illegal_chars else "" for c in cleaned_text)

            # Generate filename with cleaned and converted characters
            filename = f"{clean_and_convert(story_title)} by {clean_and_convert(story_author)}.pdf"

            # Replace comma with " and" if it exists in the author's name
            filename = filename.replace(",", " and") if "," in story_author else filename

            # Remove double spaces
            filename = " ".join(filename.split())

            # Check if the PDF file already exists in the temporary directory

            # Create the download folder in the temporary directory
            temp_dir = os.path.join(os.environ["TEMP"], "GTSWorldDL", f"Mode - {action}")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Set the output file path to the Downloads folder with the story ID as the filename
            temp_output_filepath = os.path.join(temp_dir, filename)

            # Check if the output file already exists and delete it if it does
            if os.path.exists(temp_output_filepath):
                os.remove(temp_output_filepath)

            try:
                # Save the page as a PDF file with the appropriate filename using the browser's "Save as PDF" option
                pdfkit.from_url(printable_url, temp_output_filepath)
            except:
                pdfkit.from_url(printable_url, temp_output_filepath, options=imageOptions)

            # The final destination path
            downloads_filepath = os.path.join(downloads_dir, filename)

            # Rest of your code remains unchanged up to this point

            # Check if the file already exists in the destination directory
            status = 0
            if os.path.exists(downloads_filepath):
                # Get the word count of the existing file
                existing_word_count = extract_word_count(downloads_filepath)

                # Get the word count of the file to be moved
                new_word_count = extract_word_count(temp_output_filepath)

                # Get the file size of the existing file
                existing_file_size = extract_file_size(downloads_filepath)

                # Get the file size of the file to be moved
                new_file_size = extract_file_size(temp_output_filepath)

                # Set thresholds for considering differences
                threshold_word_difference = 200  # You can adjust this threshold based on your requirements
                threshold_size_difference = 100 * 1024  # You can adjust this threshold based on your requirements

                # Compare word counts and file sizes and decide whether to overwrite or not
                if (
                    new_word_count is not None 
                    and new_word_count + threshold_word_difference < existing_word_count
                    and new_file_size is not None
                    and new_file_size + threshold_size_difference < existing_file_size
                ):
                    # File should not be overwritten
                    status = "Warning: Skipped!"
                    with open("log.txt", "a") as log_file:
                        log_file.write(f"Skipped: {filename}\n\tOld Word Count: {existing_word_count}\n\tNew Word Count: {new_word_count}\n\tOld Size: {round(existing_file_size/1024, 2)} KB\n\tNew Size: {round(new_file_size/1024, 2)} KB\n\tMode: {action}\n\tTimestamp: {datetime.datetime.now()}\n\n")
                    # Delete the new file in the temp directory
                    os.remove(temp_output_filepath)
                else:
                    # Move the downloaded PDF file to the appropriate folder in the "Downloads" folder
                    status = "Overwritten"
                    shutil.move(temp_output_filepath, downloads_filepath)
            else:
                # Move the downloaded PDF file to the appropriate folder in the "Downloads" folder
                status = "New"
                shutil.move(temp_output_filepath, downloads_filepath)

            # Print a message indicating that the file has been saved
            print(f"Processed {filename} ({i+1}/{len(story_ids)}) <{status}>")

cookies = parseCookieFile("cookies.txt")  # replace the filename

if len(sys.argv) == 1:
    # If no additional arguments are provided, ask for the download directory first
    downloads_dir = input("Enter the download directory: ")

    # Ask for the mode (individual or file)
    while True:
        mode_input = input("Enter mode (individual or file): ").lower()
        if mode_input in ["individual", "file"]:
            mode = mode_input
            break
        else:
            print("Invalid mode. Please enter 'individual' or 'file'.")

    story_ids = []

    if mode == "file":
        storylist = input("Enter the path to the file containing Story IDs: ")

        # open the file containing the links
        with open(storylist.strip('"'), 'r') as file:
            # loop through each line in the file
            for line in file:
                # use regular expressions to extract the number after uid=
                match = re.search('sid=(\d+)', line)
                # if a match is found, add the number to the array
                if match:
                    story_ids.append(int(match.group(1)))
    else:
        counter = 1
        while True:
            print(f"Enter Story ID #{counter} (press Enter to finish): ", end="")
            user_input = input()
            if not user_input:
                print("Submitting Story List")
                break
            counter += 1
            story_ids.append(user_input)

    downloadStories(action="list", storylist=story_ids, downloads_dir=downloads_dir)

if len(sys.argv) > 1 and sys.argv[1] == "--favStories":

    if len(sys.argv) > 2:
        user = sys.argv[2]
    else:
        user = 123456
    
    # Loop through the story links and download the PDFs
    downloads_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Downloads",
        "Users Favourite Stories",
        f"{uidToAuth(user)}(s) Favourite Stories",
    )
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)

    downloadStories(action="favst", uid=user, downloads_dir=downloads_dir)

if len(sys.argv) > 1 and sys.argv[1] == "--favAuth":

    author_links = []
    author_ids = []

    # Loop through the pages and extract the stories
    current_auth_page = 0

    # Set the URL template of the restricted webpage with a placeholder for the offset parameter
    if len(sys.argv) > 2:
        user = {sys.argv[2]}
    else:
        user = 123456

    base_auth_url = f"https://www.[REDACTED].net/viewuser.php?action=favau&uid={user}&offset="

    while True:

        # Set the URL of the current page
        auth_url = base_auth_url + str(current_auth_page * 20)

        # Send a GET request to the current page with the cookies
        response = make_request_with_retries(auth_url, cookies)

        # Check if the access was successful by searching for the error message
        if "You are not authorized to access that function." in response.text:
            print(f"Access to page {current_auth_page + 1} was unsuccessful.")
            break

        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the div with id "profile"
        profile_div = soup.find("div", {"id": "profile"})

        # Iterate through all anchor tags within the div with id "profile"
        for authors in profile_div.find_all("a"):
            if "viewuser.php?uid=" in authors["href"] and "contact.php" not in authors["href"]:
                # Extract the author name from the anchor tag text
                author_name = authors.text.strip()

                # Append the author link to the author_links array
                author_links.append(authors["href"])

        # Extract author IDs from the author_links array
        author_ids = [link.split("uid=")[-1] for link in author_links]

        # Check if there are more pages by looking for the "next" button
        next_button = soup.find("a", string="[Next]")
        if not next_button:
            break

        # Increment the page number to go to the next page
        current_auth_page += 1

        
    author_counter = 1

    print(f"\nUser {uidToAuth(user)} has {len(author_ids)} favourite authors.")

    for author_id in author_ids:

        # Loop through the story links and download the PDFs
        downloads_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Downloads",
            "Stories by Users Favourite Authors",
            f"{uidToAuth(user)}(s) Favourite Authors",
            f"Stories by {uidToAuth(author_id)}",
        )
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        downloadStories(action="storiesby", uid=author_id, downloads_dir=downloads_dir)

        print(f"Stories from Author {uidToAuth(author_id)} has been processed ({author_counter}/{len(author_ids)})\n")
        author_counter += 1

if len(sys.argv) > 1 and sys.argv[1] == "--archiveAuth":

    mode = 0
    author_ids = []

    if len(sys.argv) > 2 and sys.argv[2] == "--file":
        mode = "file"
        if len(sys.argv) > 3:
            authorslist = sys.argv[3]
        else:
            authorslist = input("Enter the path to the file containing User IDs: ")

        # open the file containing the links
        with open(authorslist.strip('"'), 'r') as file:
            # loop through each line in the file
            for line in file:
                # use regular expressions to extract the number after uid=
                match = re.search('uid=(\d+)', line)
                # if a match is found, add the number to the array
                if match:
                    author_ids.append(int(match.group(1)))

    else:
        mode = "individual"

        if len(sys.argv) > 2:
            # If additional arguments are provided, append them starting from argv[2]
            author_ids.extend(sys.argv[2:])
        else:
            # If no additional arguments are provided, ask the user to input User IDs
            counter = 1
            while True:
                print(f"Enter User ID #{counter}: ", end="")
                user_input = input()
                if not user_input:
                    print("Submitting Author List")
                    break
                counter += 1
                author_ids.append(user_input)

    print(f"\nThere are {len(author_ids)} authors in this list.")

    author_counter = 1

    for author_id in author_ids:

        # Loop through the story links and download the PDFs
        downloads_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Downloads",
            "Archives",
            "Stories by Authors",
            f"Stories by {uidToAuth(author_id)}",
        )
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        downloadStories(action="storiesby", uid=author_id, downloads_dir=downloads_dir)

        print(f"Stories from Author {uidToAuth(author_id)} has been processed ({author_counter}/{len(author_ids)})\n")
        author_counter += 1

if len(sys.argv) > 1 and sys.argv[1] == "--archiveStories":

    mode = 0
    story_ids = []

    if len(sys.argv) > 2 and sys.argv[2] == "--file":
        mode = "file"
        if len(sys.argv) > 3:
            storylist = sys.argv[3]
        else:
            storylist = input("Enter the path to the file containing Story IDs: ")

        # open the file containing the links
        with open(storylist.strip('"'), 'r') as file:
            # loop through each line in the file
            for line in file:
                # use regular expressions to extract the number after uid=
                match = re.search('sid=(\d+)', line)
                # if a match is found, add the number to the array
                if match:
                    story_ids.append(int(match.group(1)))

    else:
        mode = "individual"

        if len(sys.argv) > 2:
            # If additional arguments are provided, append them starting from argv[2]
            story_ids.extend(sys.argv[2:])
        else:
            # If no additional arguments are provided, ask the user to input User IDs
            counter = 1
            while True:
                print(f"Enter Story ID #{counter}: ", end="")
                user_input = input()
                if not user_input:
                    print("Submitting Story List")
                    break
                counter += 1
                story_ids.append(user_input)

    # Loop through the story links and download the PDFs
    downloads_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Downloads",
        "Archives",
        "Select Assorted Stories",
    )
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir) 

    downloadStories(action="list", storylist=story_ids, downloads_dir=downloads_dir)
