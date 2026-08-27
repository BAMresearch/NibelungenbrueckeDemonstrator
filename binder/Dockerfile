FROM quay.io/jupyter/base-notebook:notebook-7.4.3

COPY . ${HOME}
USER root

# Install system dependencies including OpenGL libs required by dolfinx/gmsh
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxft2 \
    libxrender1 \
    libxext6 \
    libgl1 \
    libglu1-mesa \
    libxi6 \
    libxinerama1 \
    libxcursor1 \
    libx11-6 \
    libxrandr2 \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN chown -R ${NB_UID} ${HOME}

USER ${NB_UID}

# Create conda environment from your environment.yml
RUN mamba env create -f binder/environment.yml && \
    conda clean --all -f -y && \
    echo "conda activate fenicsx-env" >> ~/.bashrc

ENV CONDA_DEFAULT_ENV=fenicsx-env
ENV PATH=/opt/conda/envs/fenicsx-env/bin:$PATH

# Install ipykernel in base and link fenicsx-env kernel for Jupyter
RUN pip install ipykernel && \
    conda run -n fenicsx-env python -m ipykernel install --user --name=fenicsx-env --display-name "Python (fenicsx-env)"