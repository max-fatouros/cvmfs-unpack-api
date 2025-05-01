# Test Image

The GitLab CI and Dockerfile here are used both as a template for users, and for integration testing of this repository. (The `test-image/.gitlab-ci.yml` file in this directory is included in the root-level `.gitlab-ci.yml` of this repository.)

## Introduction

The `test-image/.gitlab-ci.yml` builds the Dockerfile in this directory using Kaniko and pushes it to this project's GitLab image repository.

It then sends an http-request for the image to be unpacked into a CVMFS repository.

## Usage

Copy the contents of this folder's `.gitlab-ci.yml` and use it in your project with your own custom Dockerfile.
