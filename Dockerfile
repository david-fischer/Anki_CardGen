FROM python:3.9-buster
RUN pip install poetry virtualenv
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false;\
    poetry add pyinstaller virtualenv;\
    python -m spacy download pt
COPY main.py pyinstaller.spec ./
COPY acg ./acg
ENTRYPOINT ["bash"]
