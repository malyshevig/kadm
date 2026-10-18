import os

from prefect import flow
from prefect.deployments import deploy
from flow import process_book

if __name__ == "__main__":
    # Создаем и применяем деплоймент одной функцией
    os.environ["PREFECT_API_URL"] = "http://127.0.0.1:4200/api"

    from prefect import flow
    from prefect.filesystems import LocalFileSystem


    from prefect import flow

    from prefect_github import GitHubRepository

    storage = GitHubRepository(
        repository="https://github.com/malyshevig/kadm.git",
        reference="main",
    )
    storage.save("github-storage")  # обязательно сохраняем

    process_book.deploy(
        name="my-deployment",
        work_pool_name="book-pool",
        storage=storage,
    )

    print("Деплоймент успешно создан!")
