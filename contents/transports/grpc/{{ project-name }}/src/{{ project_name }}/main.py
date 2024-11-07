import logging
import os
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

{% for item in packages %}import {{ project_name }}.{{ item.package_name }}.{{ item.package_name }} as {{ item.package_name }}
{% endfor %}
import {{ project_name }}.utils.configuration as configuration
from {{ project_name }}.grpc import {{ project_name }}_pb2_grpc
from {{ project_name }}.grpc.{{ project_name }}_pb2 import *

configuration.configure_logging()

logger = logging.getLogger(__name__)


class {{ ProjectName }}({{ project_name }}_pb2_grpc.{{ ProjectName }}Servicer):
    def Get{{ ProjectPrefix | pluralize }}(self, request, context):
        return Get{{ ProjectPrefix | pluralize }}Response({{ project_prefix }}=[], has_next=False, has_previous=False, next_page=0,
                                previous_page=0, total_pages=0, total_elements=0)

    def Get{{ ProjectPrefix }}(self, request, context):
        dto = {{ ProjectPrefix }}Dto(name="Example")
        dto.id.value = 'id'
        return Get{{ ProjectPrefix }}Response({{ projectPrefix }}=dto)

    def Update{{ ProjectPrefix }}(self, request, context):
        return Update{{ ProjectPrefix }}Response({{ projectPrefix }}={{ ProjectPrefix }}Dto(id=request.id, name=request.name))

    def Create{{ ProjectPrefix }}(self, request, context):
        return Create{{ ProjectPrefix }}Response({{ projectPrefix }}={{ ProjectPrefix }}Dto(name=request.name))


def main():
    logger.info("Starting {{ project-title }}")

    port = os.environ.get("SERVER_PORT", "8080")
    grpc_workers = int(os.environ.get("GRPC_WORKERS", "10"))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=grpc_workers))
    {{ project_name }}_pb2_grpc.add_{{ ProjectName }}Servicer_to_server({{ ProjectName }}(), server)
    service_names = (
        DESCRIPTOR.services_by_name["{{ ProjectName }}"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
    server.add_insecure_port("[::]:{}".format(port))
    server.start()
    logger.info("{{ project-title }} started on port {}".format(port))
    server.wait_for_termination()


if __name__ == '__main__':
    main()