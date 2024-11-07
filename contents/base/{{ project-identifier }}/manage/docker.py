import subprocess


def docker_build():
    print("Creating docker image")
    subprocess.run(["docker", "build", "-t", "{{ project-identifier }}", "."])


def docker_run():
    print("Running docker image")
    subprocess.run(
        [
            "docker",
            "run",
            "-p",
            "8000:8000",  # Port mapping
            "-it",
            "{{ project-identifier }}",
        ]
    )
