from setuptools import setup


def get_requirements():
    with open("requirements.txt", "r") as file:
        reqs = [req.strip() for req in file.readlines()]
    for i, line in enumerate(reqs):
        if line.startswith("git+"):
            dep_name = line.rsplit("/")[-1].rsplit(".")[0].lower()
            reqs[i] = f"{dep_name} @ {line}"
    return [req for req in reqs if req]


setup(
    name="acg",
    version="1.0.8",
    package_dir={"acg": "acg"},
    packages=["acg", "acg.google_images_download", "acg.custom_widgets", "acg.screens"],
    include_package_data=True,
    install_requires=get_requirements(),
    entry_points={"gui_scripts": ["acg = acg.main:main",]},
    url="https://github.com/david-fischer/Anki_CardGen",
    keywords="kivy, anki, flash cards, languages, portuguese, learning",
    license="MIT",
    author="david-fischer",
    author_email="d.fischer.git@posteo.de",
    description="Kivy application to generate flash cards for Anki",
)
