import sys
import re
import os
import shutil
import requests
from bs4 import BeautifulSoup
import pdfkit
from requests.exceptions import ChunkedEncodingError
import time

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

path_wkhtmltopdf = r'.\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

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

cookies = parseCookieFile("cookies.txt")  # replace the filename


# Initialize the arrays to store the stories


if len(sys.argv) > 1 and sys.argv[1] == "--favStories":

    story_titles = []
    story_authors = []
    story_links = []
    story_ids = []

    # Create the Downloads/Favourite Stories folder in the temporary directory
    temp_dir = os.path.join(os.environ["TEMP"], "Favourite Stories")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Loop through the pages and extract the stories
    current_num = 0

    # Set the URL template of the restricted webpage with a placeholder for the offset parameter
    base_url = "https://www.[REDACTED].net/user.php?action=favst&uid=130611&offset="

    while True:

        # Set the URL of the current page
        url = base_url + str(current_num * 20)

        # Send a GET request to the current page with the cookies
        response = make_request_with_retries(url, cookies)

        # Check if the access was successful by searching for the error message
        if "You are not authorized to access that function." in response.text:
            print(f"Access to page {current_num + 1} was unsuccessful.")
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

    # Print the number of stories found

    print(f"\nFound {len(story_titles)} Stories.")

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

    # Loop through the story links and download the PDFs
    downloads_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "Downloads", "Favourite Stories"
    )
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)

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

        # Replace any characters that are not allowed in filenames with underscores
        valid_chars = (
            "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
        filename = "".join(
            c if c in valid_chars else "_"
            for c in f"{story_title} by {story_author}.pdf"
        )
        # Check if the PDF file already exists in the temporary directory

        # Set the output file path to the Downloads folder with the story ID as the filename
        temp_output_filepath = os.path.join(temp_dir, filename)

        # Check if the output file already exists and delete it if it does
        if os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)

        # Save the page as a PDF file with the appropriate filename using the browser's "Save as PDF" option
        pdfkit.from_url(printable_url, temp_output_filepath, configuration=config)

        # Move the downloaded PDF file to the "Favourite Stories" folder in the "Downloads" folder
        downloads_filepath = os.path.join(downloads_dir, filename)
        shutil.move(temp_output_filepath, downloads_filepath)

        # Print a message indicating that the file has been saved
        print(f"Saved {filename} ({i+1}/{len(story_ids)})")


elif len(sys.argv) > 1 and sys.argv[1] == "--favAuth":

    author_links = []
    author_ids = []

    # Create the Downloads/Favourite Stories folder in the temporary directory
    temp_dir = os.path.join(os.environ["TEMP"], "Favourite Authors Stories")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Loop through the pages and extract the stories
    current_auth_page = 0

    # Set the URL template of the restricted webpage with a placeholder for the offset parameter
    base_auth_url = (
        "https://www.[REDACTED].net/viewuser.php?action=favau&uid=130611&offset="
    )
    base_url = (
        "https://www.[REDACTED].net/viewuser.php?action=storiesby&uid={}&offset={}"
    )

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

        for authors in profile_div.find_all("a"):
            if (
                "viewuser.php?uid=" in authors["href"]
                and "contact.php" not in authors["href"]
            ):
                author_links.append(authors["href"])

        author_ids = [link.split("uid=")[-1] for link in author_links]

        # Check if there are more pages by looking for the "next" button
        next_button = soup.find("a", string="[Next]")
        if not next_button:
            break

        # Increment the page number to go to the next page
        current_auth_page += 1

    
    author_counter = 1
    for author_id in author_ids:

        current_num = 0
        story_titles = []
        story_authors = []
        story_links = []
        story_ids = []

        while True:

            # Set the URL of the current page
            url = base_url.format(author_id, current_num * 20)

            # Send a GET request to the current page with the cookies
            response = make_request_with_retries(url, cookies)

            # Check if the access was successful by searching for the error message
            if "You are not authorized to access that function." in response.text:
                print(
                    f"Access to page {current_num + 1} of author {author_id} was unsuccessful."
                )
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
            # Loop through each story ID and save the printable version as a PDF

        print(f"\nAuthor {story_authors[0]} has {len(story_ids)} stories")

        # Loop through the story links and download the PDFs
        downloads_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Downloads",
            "Favourite Authors Stories",
            "".join(story_authors[0]),
        )
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

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

            # Replace any characters that are not allowed in filenames with underscores
            valid_chars = (
                "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )
            filename = "".join(
                c if c in valid_chars else "_"
                for c in f"{story_title} by {story_author}.pdf"
            )
            # Check if the PDF file already exists in the temporary directory

            # Set the output file path to the Downloads folder with the story ID as the filename
            temp_output_filepath = os.path.join(temp_dir, filename)

            # Check if the output file already exists and delete it if it does
            if os.path.exists(temp_output_filepath):
                os.remove(temp_output_filepath)

            # Save the page as a PDF file with the appropriate filename using the browser's "Save as PDF" option
            pdfkit.from_url(printable_url, temp_output_filepath, configuration=config)

            # Move the downloaded PDF file to the "Favourite Stories" folder in the "Downloads" folder
            downloads_filepath = os.path.join(downloads_dir, filename)
            shutil.move(temp_output_filepath, downloads_filepath)

            # Print a message indicating that the file has been saved
            print(f"Saved {filename} ({i+1}/{len(story_ids)})")

        print(f"\nStories from Author {story_authors[0]} has been downloaded ({author_counter}/{len(author_ids)}) ")
        author_counter += 1

elif len(sys.argv) > 1 and sys.argv[1] == "--archiveAuth":

    author_ids = []

    # Create the Downloads/Favourite Stories folder in the temporary directory
    temp_dir = os.path.join(os.environ["TEMP"], "Archives\Authors Stories")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Set the URL template of the restricted webpage with a placeholder for the offset parameter

    base_url = (
        "https://www.[REDACTED].net/viewuser.php?action=storiesby&uid={}&offset={}"
    )

    # open the file containing the links
    with open('Authors.txt', 'r') as file:
        # loop through each line in the file
        for line in file:
            # use regular expressions to extract the number after uid=
            match = re.search('uid=(\d+)', line)
            # if a match is found, add the number to the array
            if match:
                author_ids.append(int(match.group(1)))

    author_counter = 1

    for author_id in author_ids:

        
        current_num = 0
        story_titles = []
        story_authors = []
        story_links = []
        story_ids = []

        while True:

            # Set the URL of the current page
            url = base_url.format(author_id, current_num * 20)

            # Send a GET request to the current page with the cookies
            response = make_request_with_retries(url, cookies)

            # Check if the access was successful by searching for the error message
            if "You are not authorized to access that function." in response.text:
                print(
                    f"Access to page {current_num + 1} of author {author_id} was unsuccessful."
                )
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
            # Loop through each story ID and save the printable version as a PDF

        print(f"\nAuthor {story_authors[0]} has {len(story_ids)} stories")

        # Loop through the story links and download the PDFs
        downloads_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Downloads",
            "Archives\Authors Stories",
            "".join(story_authors[0]),
        )
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

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

            # Replace any characters that are not allowed in filenames with underscores
            valid_chars = (
                "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )
            filename = "".join(
                c if c in valid_chars else "_"
                for c in f"{story_title} by {story_author}.pdf"
            )
            # Check if the PDF file already exists in the temporary directory

            # Set the output file path to the Downloads folder with the story ID as the filename
            temp_output_filepath = os.path.join(temp_dir, filename)

            # Check if the output file already exists and delete it if it does
            if os.path.exists(temp_output_filepath):
                os.remove(temp_output_filepath)

            # Save the page as a PDF file with the appropriate filename using the browser's "Save as PDF" option
            pdfkit.from_url(printable_url, temp_output_filepath, configuration=config)

            # Move the downloaded PDF file to the "Favourite Stories" folder in the "Downloads" folder
            downloads_filepath = os.path.join(downloads_dir, filename)
            shutil.move(temp_output_filepath, downloads_filepath)

            # Print a message indicating that the file has been saved
            print(f"Saved {filename} ({i+1}/{len(story_ids)})")
        
        print(f"\nStories from Author {story_authors[0]} has been downloaded ({author_counter}/{len(author_ids)}) ")
        author_counter += 1

elif len(sys.argv) > 1 and sys.argv[1] == "--archiveStories":

    story_titles = []
    story_authors = []
    story_ids = []

    # Create the Downloads/Favourite Stories folder in the temporary directory
    temp_dir = os.path.join(os.environ["TEMP"], "Archives\Individual Stories")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # open the file containing the links
    with open('Stories.txt', 'r') as file:
        # loop through each line in the file
        for line in file:
            # use regular expressions to extract the number after uid=
            match = re.search('sid=(\d+)', line)
            # if a match is found, add the number to the array
            if match:
                story_ids.append(int(match.group(1)))
    

    # Print the number of stories found

    print(f"\nFound {len(story_ids)} Stories.")

    # Loop through the story links and download the PDFs
    downloads_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "Downloads", "Archives\Individual Stories"
    )
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)

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

        # Replace any characters that are not allowed in filenames with underscores
        valid_chars = (
            "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
        filename = "".join(
            c if c in valid_chars else "_"
            for c in f"{story_title} by {story_author}.pdf"
        )
        # Check if the PDF file already exists in the temporary directory

        # Set the output file path to the Downloads folder with the story ID as the filename
        temp_output_filepath = os.path.join(temp_dir, filename)

        # Check if the output file already exists and delete it if it does
        if os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)

        # Save the page as a PDF file with the appropriate filename using the browser's "Save as PDF" option
        pdfkit.from_url(printable_url, temp_output_filepath, configuration=config)

        # Move the downloaded PDF file to the "Favourite Stories" folder in the "Downloads" folder
        downloads_filepath = os.path.join(downloads_dir, filename)
        shutil.move(temp_output_filepath, downloads_filepath)

        # Print a message indicating that the file has been saved
        print(f"Saved {filename} ({i+1}/{len(story_ids)})")