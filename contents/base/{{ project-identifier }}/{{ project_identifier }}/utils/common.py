import re
from loguru import logger
from collections import defaultdict

import logging
from datetime import datetime

from {{ project_identifier }}.utils.chat_profiles import CHAT_PROFILES


class ScriptTimer:
    """
    Measures the execution time of a script.

    Usage:
    ```
    with ScriptTimer('My logging message'):
        # code to be timed
    ```
    """

    def __init__(self, name, logger=None):
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info("★")
        self.logger.info(f"● {self.name} started at {self.start_time}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        self.logger.info(f"● {self.name} completed in {duration}")
        self.logger.info("┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉")


class MetadataExtractor:
    """
    MetadataExtractor is a class designed to extract specific metadata from a given response_metadata object.

    Attributes:
        response_metadata (dict): The metadata extracted from the response object.
        score (float or None): The score associated with the response, if available.

    Methods:
        extract_image_path():
            Extracts the image path from the metadata.
            Returns:
                str: The relative path to the image if found, otherwise None.

        extract_document_path():
            Extracts the document path from the metadata.
            Returns:
                str: The relative path to the document if found, otherwise None.

        extract_page_number():
            Extracts the page number from the metadata.
            Returns:
                str: The page number as a string, or "Unknown" if not found.

        extract_parsed_text():
            Extracts the parsed text in markdown format from the metadata.
            Returns:
                str: The parsed text if found, otherwise "No parsed text found."
    """

    def __init__(self, response_metadata):
        # Assuming response_metadata is an instance of NodeWithScore, extract the node metadata
        self.response_metadata = (
            response_metadata.node.metadata if hasattr(response_metadata, "node") else response_metadata
        )
        self.score = response_metadata.score if hasattr(response_metadata, "score") else None

    def extract_image_path(self):
        pattern = r".*/data/images/(.*)"
        try:
            image_path = re.findall(pattern, self.response_metadata.get("image_path", ""))[0]
            return f"./data/images/{image_path}"
        except (IndexError, AttributeError):
            logger.info("No valid image path found.")
            return None

    def extract_document_path(self):
        pattern_file = r".*/data/documents/(.*)"
        try:
            file_path = re.findall(pattern_file, self.response_metadata.get("source_file_path", ""))[0]
            return f"./data/documents/{file_path}"
        except (IndexError, AttributeError):
            logger.info(f"No source document path match for {self.response_metadata.get('source_file_path', None)}.")
            return None

    def extract_page_number(self):
        return str(self.response_metadata.get("page_num", "Unknown"))

    def extract_parsed_text(self):
        return self.response_metadata.get("parsed_text_markdown", "No parsed text found.")


def process_response_metadata_list(response_metadata_list):
    """
    Processes a list of response metadata and organizes the extracted information into a structured format.

    Args:
        response_metadata_list (list): A list of response metadata dictionaries to be processed.

    Returns:
        list: A list of dictionaries, each representing a document with the following keys:
            - type (str): The type of the document, default is "Pdf".
            - path (str): The file path of the document.
            - name (str): The name of the document.
            - display (str): Display mode, default is "inline".
            - page_numbers (list): A sorted list of page numbers where the document appears.
            - text (list): A list of parsed text segments from the document.
            - score (float): The highest score associated with the document.
            - images (list): A list of dictionaries, each representing an image with the following keys:
                - type (str): The type of the image, default is "Image".
                - path (str): The file path of the image.
                - name (str): The name of the image.
                - display (str): Display mode, default is "inline".
                - page_num (int): The page number where the image appears.
                - text (str): The parsed text associated with the image.
                - score (float): The score associated with the image.
    """
    all_documents = defaultdict(
        lambda: {
            "type": "Pdf",
            "path": None,
            "name": None,
            "display": "inline",
            "page_numbers": set(),
            "text": "",
            "score": None,
            "images": [],
        }
    )

    for index, response_meta in enumerate(response_metadata_list):
        extractor = MetadataExtractor(response_meta)

        final_image_path = extractor.extract_image_path()
        final_document_path = extractor.extract_document_path()
        page_number = extractor.extract_page_number()
        parsed_text = extractor.extract_parsed_text()
        score = extractor.score

        if final_document_path:
            document = all_documents[final_document_path]
            document["path"] = final_document_path
            document["name"] = f"pdf{len(all_documents)}"
            document["page_numbers"].add(page_number)
            document["text"] += parsed_text + "\n\n"
            document["score"] = score if document["score"] is None else max(document["score"], score)

            if final_image_path:
                document["images"].append(
                    {
                        "type": "Image",
                        "path": final_image_path,
                        "name": f"image{len(document['images']) + 1}",
                        "display": "inline",
                        "page_num": page_number,
                        "score": score,
                    }
                )

    # Convert page_numbers from set to sorted list for consistency
    for document in all_documents.values():
        document["page_numbers"] = sorted(document["page_numbers"])

    return list(all_documents.values())


async def find_profile_data(chat_profile):
    """
    Searches for a chat profile by name in the CHAT_PROFILES dictionary.

    Args:
        chat_profile (str): The name of the chat profile to search for.

    Returns:
        dict or None: The profile dictionary if a match is found, otherwise None.
    """
    for profile in CHAT_PROFILES.values():
        if profile.get("name") == chat_profile:
            # Return the persona_type if a match is found
            return profile
    return None
