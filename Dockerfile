FROM python:3.9-buster
RUN pip install poetry virtualenv
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false;\
    poetry add pyinstaller;\
    poetry install --no-dev --no-root --no-interaction --no-ansi;\
    python -m spacy download pt
COPY main.py pyinstaller.spec README.md ./
COPY acg ./acg
ENTRYPOINT ["bash"]
