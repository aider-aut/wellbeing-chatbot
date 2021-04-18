
# Extend the official Rasa SDK image
FROM rasa/rasa-sdk:2.5.0



# make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Use subdirectory as working directory
WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:/app/
ENV PYTHONPATH=${PYTHONPATH}:/app/custom_component

# Copy any additional custom requirements, if necessary (uncomment next line)
# COPY actions/requirements-actions.txt ./

# Change back to root user to install dependencies
USER root

# install dependencies
RUN pip install -U pip setuptools wheel
RUN pip install -U spacy
RUN pip install rasa[spacy]
RUN python -m spacy download en_core_web_md
RUN python -m spacy link en_core_web_md en

# Install extra requirements for actions code, if necessary (uncomment next line)
# RUN pip install -r requirements-actions.txt

# Copy actions folder to working directory
COPY ./actions /app/actions
COPY ./custom_component /app/custom_component

# By best practices, don't run the code with root user
USER 1001
