# Unpack to CVMFS

This repository unpacks (unzips) and syncs (pushes) container images to a [Cern Virtual Machine File System (CVMFS)](https://cvmfs.readthedocs.io/en/stable/) repository using the [Daemon that Unpacks Container Images into CernVM-FS (DUCC)](https://cvmfs.readthedocs.io/en/stable/cpt-ducc.html).

> **NOTE**
> This repository is a template. An instance of it can be configured to synchronize a CVMFS repository of your choosing.
>
> Instruction on how to set up this repository are found in the [Configuring this Repository](#configuring-this-repository) section.
>
> Once this template has been instantiated
>
> - [ ] Delete the [Configuring this Repository](#configuring-this-repository) section.
> - [ ] Customize this `README.md` with any relavent information for the users.
> - [ ] Delete this note. (not the one below please)

> **NOTE** This repository was created from a template.
> If you would like to make an instance of your own CVMFS unpacking repository, please [create a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) from&mdash;or copy from&mdash;the template repository: https://github.com/cvmfs-contrib/cvmfs-unpack-api

## Introduction

CVMFS handles distributing software (including container images) to users.
It provides decompressed copies of these images for users to run with tools like [Apptainer](https://apptainer.org/) (formerly singularity), or the [CVMFS Containerd Snapshotter](https://github.com/cvmfs/cvmfs/tree/devel/snapshotter)

This repository periodically unpacks the list of images in the [recipe.yaml](recipe.yaml) file via a scheduled GitLab pipeline to the cvmfs repository defined in the recipe.

This scheduled unpacking operates very similarly to how CERN unpacks images to their `unpacked.cern.ch` CVMFS repository via the following two git repositories:

- https://gitlab.cern.ch/unpacked/sync/-/tree/master
- https://github.com/cvmfs/images-unpacked.cern.ch/tree/master

In addition to scheduled synchronization, this repository also accepts http-requests to synchronize images on-demand.
This allows users to request from a CI pipeline that their image be synced with CVMFS.
This can be done immediately after building and pushing that image to an image-repository from the same CI pipeline.

### Project Structure

<pre>
.
│   # Image to test building and unpacking to CVMFS
│   # through the GitLab CI in this repository.
├── <b><a href=test-image>test-image/</a></b>
│
│   # List of images to periodically unpack to a CVMFS server.
│   # Read more about the syntax <a href=https://cvmfs.readthedocs.io/en/stable/cpt-containers.html#image-wishlist-syntax>here</a>.
├── <b><a href=recipe.yaml>recipe.yaml</a></b>
│
│   # Server to authenticate unpack-on-demand http-requests.
└── <b><a href=unpack-api>unpack-api/</a></b>
</pre>

## Usage

Users can request to have their images unpacked to a CVMFS repository in one of three ways. Each method is independent of one another and users can choose multiple methods if they wish.

### Scheduled Unpacking

To register an image for periodic unpacking, add an image to the [`recipe.yaml`](recipe.yaml) following the syntax described [here](https://cvmfs.readthedocs.io/en/stable/cpt-containers.html#image-wishlist-syntax).

### On-Demand Unpacking from a GitLab CI / GitHub Action

#### GitLab CI

> **NOTE** The CI files we include are only available from gitlab.cern.ch

To see how we build, push, and unpack a [`test-image/`](test-image), see [`test-image/.gitlab-ci.yml`](test-image/.gitlab-ci.yml).

Otherwise, copy the contents of this `main.yml` file to your GitLab CI

<details>
<summary> <code>.gitlab-ci.yml</code></summary>

```yaml
include:
  - project: 'https://gitlab.cern.ch/ci-tools/container-image-ci-templates'
    file: 'kaniko-image.gitlab-ci.yml'
  - project: 'https://gitlab.cern.ch/mfatouro/unpack-to-cvmfs'
    file: 'test-image/.gitlab-ci.yml'

stages:
  - build
  - notify


variables:
  IMAGE: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"


build_and_push:
  stage: build
  extends: .build_kaniko
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
  tags:  # overrides the tags of .build_kaniko
    - docker
  variables:
    REGISTRY_IMAGE_PATH: "${IMAGE}"
    PUSH_IMAGE: "true"


notify_ducc:
  stage: notify
  extends: .notify_ducc
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
  tags:
    - shell
    - authentication-server
  variables:
    IMAGE: "${IMAGE}"
    EXTRA_TAGS: 'latest'
    AUTHENTICATION_SERVER: 0.0.0.0
```

</details>

#### Github Action

### On-Demand Unpacking from an HTTP-Request

Apart from being called from a GitLab CI, the `unpack-api` server api can also be called from an http-request.

> **NOTE**
>
> Password-authenticated http-requests are disabled by default.
>
> HTTP-requests are only enabled if the `unpack-api` server is configured with
> a `SECRET_TOKEN` in the `unpack-api/.env` file.
> (See [`unpack-api/.env.sample`](unpack-api/.env.sample).)

Request for your image to be unpacked with

```bash
curl \
    -X "POST" \
    -H "Authorization:<secret_token>" \
    "<server_ip>:8000/api/sync/secret?image=<image>"
```

where

- `<secret_token>` is the `SECRET_TOKEN` configured for the `unpack-api` server.
- `<server_ip>` is the ip address of the `unpack-api` server.
- `<image>` is the full image name to be unpacked.
  - e.g. gitlab-registry.cern.ch/mfatouro/unpack-to-cvmfs/test-image:latest

## Terminology

- **CI**: Continuous Integration.
- **CVMFS:** Cern Virtual Machine File System.
- **Container Image:** A term that includes, but is not limited to, a docker image.
- **DUCC:** Daemon that Unpacks Container Images into CernVM-FS
- **Sync:** Push an unzipped container image to a CVMFS repository.
- **Unpack:** Unzip a container image.

## Configuring this Repository

> **NOTE** Relevant for administrators only

On the machine running the CVMFS server, add the following to `/etc/sudoers.d/cvmfs_ducc`

```
gitlab-runner ALL=(ALL) NOPASSWD:SETENV: /usr/bin/cvmfs_ducc
gitlab-runner ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop autofs
```

So that the commands can be ran from the GitLab CI without a sudo password.
