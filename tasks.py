import platform

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
def clean_app(c):
    c.run("buildozer appclean")


@task
def readme(c):
    c.run("python .utils/render_readme.py")


@task
def run(c):
    c.run("buildozer debug deploy run")
    c.run("adb logcat | grep python")
