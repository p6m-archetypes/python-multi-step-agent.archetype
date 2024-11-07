import logging
import {{ project_name}}.utils.configuration as configuration

{% for item in packages %}import {{ project_name }}.{{ item.package_name }}.{{ item.package_name }} as {{ item.package_name }}
{% endfor %}

configuration.configure_logging()

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting {{ project-title }}")

    {% for item in packages %}{{ item.package_name }}.execute()
    {% endfor %}

    logger.info("Finished {{ project-title }}")


if __name__ == '__main__':
    main()