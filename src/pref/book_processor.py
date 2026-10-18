import logging

from prefect.deployments import run_deployment
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")


class BookProcessor:

    def __init__(self, deployment):
        self.deployment_name = deployment


    async def process_file (self, uuid):
        flow_run = await run_deployment(
            name=f"process_book/{self.deployment_name}",
            parameters={"file_uuid": uuid},
            timeout=0,  # timeout=0 означает "не ждать завершения, вернуть управление сразу"
            tags=["process_book"]  # Опциональные теги для фильтрации в UI
        )
        logger.info(f"started flow {flow_run}")


if __name__ == "__main__":
    BookProcessor("default").process_file("1234")