from setuptools import setup


def get_requirements():
    with open("requirements.txt", "r") as file:
        reqs = [req.strip() for req in file.readlines()]
    return [req for req in reqs if req]


print(f"requirements: {get_requirements()}")

setup(
    name="ACG",
    version="1.0.5",
    packages=["acg"],
    package_dir={"acg": "src"},
    include_package_data=True,
    install_requires=get_requirements(),
    url="https://github.com/david-fischer/Anki_CardGen",
    keywords="kivy, anki, flash cards, languages, portuguese, learning",
    license="MIT",
    author="david-fischer",
    author_email="d.fischer.git@posteo.de",
    description="Kivy application to generate flash cards for Anki",
)
