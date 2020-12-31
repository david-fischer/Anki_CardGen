import platform
import re

from invoke import task

OPEN_CMD = "xdg-open" if platform.system() == "Linux" else "open"


@task
def clean_docs(c):
    c.run("make -C docs clean")


@task(clean_docs)
def docs(c):
    c.run("make -C docs html")
    c.run(f"{OPEN_CMD} docs/_build/html/index.html")


@task
def get_deps(c):
    a = c.run("poetry export -f requirements.txt --without-hashes", hide="out")
    reqs = [line.split(";")[0] for line in a.stdout.splitlines()]
    for i, req in enumerate(reqs):
        if " @ " in req:
            reqs[i] = req.split(" @ ")[-1]
    return ",".join(reqs)


@task
def update_buildozer_reqs(c):
    with open("buildozer.spec") as file:
        buildozer_spec = file.read()

    buildozer_spec = re.sub(
        r"(^requirements\s*=)(.*)",
        fr"\1 {get_deps(c)}",
        buildozer_spec,
        flags=re.MULTILINE,
    )
    with open("buildozer.spec", "w") as file:
        file.write(buildozer_spec)


@task
def clean_app(c):
    c.run("buildozer appclean")


@task()
def readme(c):
    c.run("python .utils/render_readme.py")


@task
def run(c):
    c.run("buildozer android debug deploy run")
    c.run("adb logcat | grep python", pty=True)


@task
def rpi_push(c):
    c.run(
        'ssh pi@nextcloudpi.local mv /home/pi/boulder-stats "/home/pi/bs_$(shell date +%F_%T)"'
    )
    c.run("scp -r ${CURDIR} pi@nextcloudpi.local:/home/pi/boulder-stats")


@task
def update_readme(c):
    c.run("python .utils/render_readme.py")
    c.run('git commit README.md -m "update: README"')
    c.run("git push origin master")


@task
def docker(c):
    c.run("sudo docker build -t boulder . -f Dockerfile")


@task
def run_docker(c):
    c.run(
        "sudo docker run --rm -d -v boulder_vol:/boulder-stats/ -t boulder:latest bot start"
    )
    c.run(
        "sudo docker run --rm -d -v boulder_vol:/boulder-stats/ -t boulder:latest data schedule"
    )
