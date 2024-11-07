import re

import logging
from pathlib import Path
import traceback
from dotenv import load_dotenv

from llama_parse import LlamaParse

from llama_index.core import VectorStoreIndex, Document, Settings

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.extractors import (
    QuestionsAnsweredExtractor,
)

load_dotenv()

# Setup models for llama_index
llm = OpenAI(model="gpt-4o", temperature=0, max_retries=10, timeout=120)
llm_mini = OpenAI(model="gpt-4o-mini", temperature=0, max_retries=10, timeout=120)
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

Settings.embed_model = embed_model
Settings.llm = llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

DATA_FOLDER_NAME = "data"
DOCUMENTS_FOLDER_NAME = "documents"
IMAGES_FOLDER_NAME = "images"
INDEX_FOLDER_NAME = "indices"

data_path = Path(__file__).resolve().parent.parent / DATA_FOLDER_NAME
data_pdf_path = data_path / DOCUMENTS_FOLDER_NAME
data_images_path = data_path / IMAGES_FOLDER_NAME
index_path = data_path / INDEX_FOLDER_NAME

# Early exit if index already exists
if index_path.exists() and any(index_path.iterdir()):
    logger.info(f"Index already exists at '{index_path}'. Exiting the script.")
    logger.info("You can delete the folder and re-run the script in order to rebuild and index.")
    exit()

# Ensure directories for the index and images exist
data_images_path.mkdir(parents=True, exist_ok=True)
index_path.mkdir(parents=True, exist_ok=True)


def get_page_number(file_name):
    match = re.search(r"-img_p(\d+)_(\d+).*", str(file_name))
    if match:
        return int(match.group(1))
    return 0


def get_image_number(file_name):
    match = re.search(r"-img_p(\d+)_(\d+).*", str(file_name))
    if match:
        return int(match.group(2))
    return 0


def _get_sorted_image_files(image_dir):
    """Get image files sorted by page."""
    raw_files = [f for f in list(Path(image_dir).iterdir()) if f.is_file()]
    sorted_files = sorted(raw_files, key=get_page_number)
    return sorted_files


def get_documents(json_dicts, image_dir=None, original_pdf_path=None):
    """Split docs into documents, attach image metadata."""
    documents = []
    image_files = _get_sorted_image_files(image_dir) if image_dir is not None else None
    md_texts = [d["md"] for d in json_dicts]
    # texts = [d["text"] for d in json_dicts]

    for idx, md_text in enumerate(md_texts):
        chunk_metadata = {"page_num": idx + 1}
        if image_files is not None and idx < len(image_files):
            image_file = image_files[idx]
            chunk_metadata["image_path"] = str(image_file)
        chunk_metadata["parsed_text_markdown"] = md_text
        chunk_metadata["source_file_path"] = original_pdf_path  # Set the original PDF path here

        node = Document(
            text=chunk_metadata["parsed_text_markdown"],  # or texts can be used.
            metadata=chunk_metadata,
            excluded_embed_metadata_keys=["page_num", "image_path", "source_file_path", "parsed_text_markdown"],
            excluded_llm_metadata_keys=["page_num", "image_path", "source_file_path", "parsed_text_markdown"],
        )
        documents.append(node)

    return documents


def parse_data_documents_and_create_index():
    """
    Parses PDF Text, Tables & Images and creates a VectorStoreIndex
    """
    parser = LlamaParse(
        verbose=True,
        result_type="markdown",
        language="en",
        num_workers=8,  # Adjust the number of workers as needed
    )

    text_documents_pool = []

    try:
        # Step 1: Collect all PDF files
        pdf_files = [file for file in Path(data_pdf_path).iterdir() if file.suffix == ".pdf"]
        logger.info(f"Found {len(pdf_files)} PDF files to process.")

        # Step 2: Parse all PDFs (parallel processing)
        json_results_list = parser.get_json_result(pdf_files)
        logger.info(f"Finished parsing {len(json_results_list)} PDFs")

        # Step 3: Iterate over the results, maintaining association with PDF files
        for pdf_file, md_json_objs in zip(pdf_files, json_results_list):
            if md_json_objs:
                md_json_list = md_json_objs["pages"]
                original_pdf_path = md_json_objs["file_path"]
                logger.info(f"Extracting images for {pdf_file.name}...")

                # Ensure a unique image directory for each PDF
                data_images_file_path = data_images_path / pdf_file.name
                data_images_file_path.mkdir(parents=True, exist_ok=True)

                # Extract images for this PDF
                image_dicts = parser.get_images([md_json_objs], download_path=data_images_file_path)
                logger.info(f"Finished extracting {len(image_dicts)} images for {pdf_file.name}")

                logger.info(f"Extracting text documents for {pdf_file.name}...")
                text_documents = get_documents(
                    md_json_list, image_dir=data_images_file_path, original_pdf_path=str(original_pdf_path)
                )
                logger.info(f"Finished extracting {len(text_documents)} text documents for {pdf_file.name}")
                text_documents_pool.extend(text_documents)
            else:
                logger.warning(f"No content extracted from {pdf_file.name}.")
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        logger.error(traceback.format_exc())

    logger.info("Building the Index...")
    vector_index = VectorStoreIndex.from_documents(
        text_documents_pool, transformations=[QuestionsAnsweredExtractor(questions=3, llm=llm_mini, num_workers=2)]
    )
    vector_index.storage_context.persist(persist_dir=index_path)
    logger.info(f"Finished building the VectorStoreIndex, saved to disk at {index_path}.")

    return vector_index


if __name__ == "__main__":
    """
    This script parses PDF documents, extracts text and images, and creates a VectorStoreIndex.
    """
    index = parse_data_documents_and_create_index()
