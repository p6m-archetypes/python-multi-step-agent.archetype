#!/bin/bash
{% if 'Phoenix' in observability %}export PHOENIX_OBSERVABILITY=true{% endif %}
chainlit run main.py -h --host 0.0.0.0 --port 8000