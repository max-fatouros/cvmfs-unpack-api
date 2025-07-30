# Unpack API

> **NOTE**
>
> This API works with both GitLab CI/CD Pipelines, and GitHub Actions workflows.
> To keeps things simple, I'll refer to both simultaneously as a **workflow** in this document.

This repository authenticates and forwards requests to unpack images into a CVMFS repository.

This API accepts the name of an image to unpack along with a workflow JWT token.
This server then forwards that image, along with a pipeline trigger token, to another workflow that performs the unpacking of the image into CVMFS.

1. Client sends request to this API from within a workflow.
1. This API authenticates the Client (ensures the pipeline was ran from within a specific GitLab/GitHub instance).
1. This API sends a request to a different workflow to unpack the image.

## Install

Using podman (or docker), run

```bash
podman create -p 8000:8000 --env-file=.env --name unpack-api  gitlab-registry.cern.ch/mfatouro/unpack-to-cvmfs/unpack-api:latest
```

Otherwise, this package can be installed with

```bash
pip install .
```

## Setup

### Configure

Copy the sample configuration

```bash
cp .env.sample .env
```

Then open .env and set the values for your use case.

### Run as a Service

First, create a docker container as shown in the [installation instructions](#install).
Then, create a `systemd` service file at `/etc/systemd/system/unpack-api.service` with the following content

```systemd
[Unit]
Description=API to authenticate and trigger a GitLab CI pipeline
Wants=syslog.service
Wants=network.target

[Service]
Restart=always
User=<user>
Group=<user>
ExecStart=/usr/bin/podman start -a unpack-api
ExecStop=/usr/bin/podman stop -t 2 unpack-api

[Install]
WantedBy=multi-user.target
```

replacing `<user>` with the user you'd like to run the service.

Finally, enable and run the service with

```bash
sudo systemctl enable unpack-api
sudo systemctl start unpack-api
```

## Contributing

Install with

```bash
pip install -e ".[dev]"
```

Then, enable [pre-commit](https://pre-commit.com/) with

```bash
pre-commit install
```
