FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# Copy environment file
COPY environment.yml .

# Create conda environment from environment.yml
RUN conda env create -f environment.yml

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "llms", "/bin/bash", "-c"]

# Expose port for Jupyter
EXPOSE 8888

# Set environment variables
ENV JUPYTER_ENABLE_LAB=yes
ENV JUPYTER_TOKEN=develop

# Start Jupyter Lab
CMD ["conda", "run", "-n", "llms", "jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--no-browser"] 