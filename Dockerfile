# SeleniumBase Docker Image
FROM ubuntu:22.04
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

#======================
# Locale Configuration
#======================
RUN apt-get update
RUN apt-get install -y --no-install-recommends tzdata locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN echo "LANG=en_US.UTF-8" > /etc/locale.conf
RUN locale-gen en_US.UTF-8

#======================
# Install Common Fonts
#======================
RUN apt-get update
RUN apt-get install -y \
    fonts-liberation \
    fonts-liberation2 \
    fonts-font-awesome \
    fonts-ubuntu \
    fonts-terminus \
    fonts-powerline \
    fonts-open-sans \
    fonts-mononoki \
    fonts-roboto \
    fonts-lato

#============================
# Install Linux Dependencies
#============================
RUN apt-get update
RUN apt-get install -y \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libu2f-udev \
    libvulkan1 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2

#==========================
# Install useful utilities
#==========================
RUN apt-get update
RUN apt-get install -y xdg-utils ca-certificates

#=================================
# Install Bash Command Line Tools
#=================================
RUN apt-get update
RUN apt-get -qy --no-install-recommends install \
    curl \
    sudo \
    unzip \
    vim \
    wget \
    xvfb

#================
# Install Chrome
#================
RUN apt-get update
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN rm ./google-chrome-stable_current_amd64.deb

#================
# Install Python
#================
RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-setuptools python3-dev python3-tk
RUN alias python=python3
RUN echo "alias python=python3" >> ~/.bashrc
RUN apt-get -qy --no-install-recommends install python3.10
RUN rm /usr/bin/python3
RUN ln -s python3.10 /usr/bin/python3

#===============================
# Install gcc (system dependency)
#===============================
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*
 
#===============
# Cleanup Lists
#===============
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

#=====================
# Set up Project
#=====================
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy your project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/automation/downloaded_files
RUN mkdir -p /app/automation/screenshots/errors
RUN mkdir -p /app/browser_data
RUN mkdir -p /app/static

# Set permissions
RUN chmod -R 777 /app/automation/downloaded_files
RUN chmod -R 777 /app/automation/screenshots/errors
RUN chmod -R 777 /app/browser_data
RUN chmod -R 777 /app/static

#=======================
# Download chromedriver
#=======================
RUN seleniumbase get chromedriver --path

#==========================================
# Create entrypoint and setup scripts
#==========================================
# COPY docker/docker-entrypoint.sh /
# COPY docker/run_docker_test_in_chrome.sh /
# RUN chmod +x /docker-entrypoint.sh /run_docker_test_in_chrome.sh
# ENTRYPOINT ["/docker-entrypoint.sh"]
# CMD ["/bin/bash"]
# Expose port and run application


# Expose the port your Flask app runs on
EXPOSE 8080

# Set the Python path so your application is discoverable
ENV PYTHONPATH=/app
ENV DISPLAY=:99


# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
# CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & gunicorn --bind 0.0.0.0:8080 app:app"]
# CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & gunicorn --bind 0.0.0.0:8080 --timeout 180 app:app"]
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & gunicorn --bind 0.0.0.0:8080 --timeout 180 --workers 3 app:app"]