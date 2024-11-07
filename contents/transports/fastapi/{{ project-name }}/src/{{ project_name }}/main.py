import logging
import {{ project_name}}.utils.configuration as configuration
import uvicorn
from fastapi import FastAPI, Query

{% for item in packages %}import {{ project_name }}.{{ item.package_name }}.{{ item.package_name }} as {{ item.package_name }}
{% endfor %}

configuration.configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # Perform initialization tasks here
    # For example, setting up a database connection, loading data, etc.
    logger.info("Starting {{ project-title }}")

    {% for item in packages %}{{ item.package_name }}.execute()
    {% endfor %}

@app.get("/echo")
async def echo(message: str = Query(None, alias="message")):
    return {"message": message}


@app.get("/health/readiness")
def health_check():
    return {"status": "healthy"}


def main():
    uvicorn.run("{{ project_name }}.main:app", host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()