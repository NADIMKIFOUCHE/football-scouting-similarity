FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Données StatsBomb, ML, visualisation terrain, appli web
RUN pip install \
    pandas \
    numpy \
    scikit-learn \
    statsbombpy \
    matplotlib \
    mplsoccer \
    streamlit

COPY . .

EXPOSE 8501

# Quand app.py existera :
# CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
CMD ["bash"]
