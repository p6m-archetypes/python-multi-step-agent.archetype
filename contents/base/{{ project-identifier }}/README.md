# Multi Step Agent ({{ project-title }})

This project comes with documents and a built index for you to test the functionality. `{{ project-identifier }}/data/documents` folder contains the pdf files we have vectorized earlier. If you would like to recreate the index with your own documents, please follow the steps in index creation section.

You can access your project here:

[https://{{ project-identifier }}.eks.us-east-2.aws.dev.{{ org-name }}-{{ solution-name }}.p6m.run](https://{{ project-identifier }}.eks.us-east-2.aws.dev.{{ org-name }}-{{ solution-name }}.p6m.run)

## Project Initialization

Before performing any actions on this project, you must first initialize it. Initialization ensures that:

- Dependencies are installed
- A virtual environment is created
- Project management commands are set up

Proper initialization ensures that the project will smoothly load into your IDE, run, build, and package correctly.

Make sure that you have a conda environment available:

```shell
conda create -n {{ project-identifier }} python=3.11
conda activate {{ project-identifier }}
```

To initialize the project, run:

```shell
poetry install
```

## Local Development

Running:

```shell
cd {{ project_identifier }}
./run.sh
```

Testing:

```shell
poetry run pytest
```

## Containerization

Building:

```shell
poetry run docker-build
```

Running:

```shell
poetry run docker-run
```

## Secrets

In your secrets manager, create a secret named `{{ project-identifier }}` and place the values below:

```shell
# OpenAI Key
OPENAI_API_KEY=<YOUR_KEY>

# For web based search
TAVILY_API_KEY=<YOUR_KEY>

# To have the chat history working
LITERAL_API_KEY=<YOUR_KEY>

# If you would like to build an index
LLAMA_CLOUD_API_KEY=<YOUR_KEY>

# You can re-create this using `chainlit create-secret`
CHAINLIT_AUTH_SECRET=<YOUR_SECRET>
```

## Extra

### Basic Authentication

This functionality is required for the chat history to be available, a dummy functionality has been implemented. You can replace this with your authentication method, e.g. oauth.

- username: admin
- password: admin

For more information please refer to: [https://docs.chainlit.io/authentication/overview](https://docs.chainlit.io/authentication/overview)

### Index Creation

- Make sure that you have the pdf files in `{{ project-identifier }}/data/documents/`
- Delete the following folders:

```shell
rm -rf {{ project-identifier }}/data/images {{ project-identifier }}/data/indices
```

- Run the following script, which will read the pdf files from the documents folder, and use LlamaParse to extract images/text and create a new index for you.

```shell
poetry run python {{ project-identifier }}/scripts/index_data.py
```

- After completing these steps, you can restart your application.
