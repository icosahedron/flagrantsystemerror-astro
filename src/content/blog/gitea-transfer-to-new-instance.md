---
title: "Gitea Transfer to New Instance"
pubDate: 2024-12-21
description: "This article describes how to move a Giteahttps://about.gitea.com instance from one docker container to another. I thought that simply copying the mounted vo…"
heroImage: "/images/covers/e9dca569a152.jpg"
heroImagePosition: 0.3068
---
This article describes how to move a [Gitea](https://about.gitea.com) instance from one docker container to another. I thought that simply copying the mounted volume directory would be sufficient, but apparently isn’t.

Gitea has a CLI that can export most of the data (excepting the projects).

Here are some articles that I read to understand how to do the transfer.

:::bookmark{url="https://forum.gitea.com/t/export-format-for-gitea/3845"}
Export format for Gitea
:::

[https://github.com/go-gitea/gitea/pull/12244](https://github.com/go-gitea/gitea/pull/12244) - PR and issue that introduced the `dump-repo` and `restore-repo` options.

Using the above it’s possible to dump the contents of the repo and restore it into another Gitea instance. (It supposedly works for other Git repos too.)

## Docker Containers

If you run Gitea in a docker container, then there are a few extra steps.

First, log in to the original docker container with `docker exec -it <container name> /bin/sh`

This will give you a shell as root. But the gitea command line program [refuses to run as root](https://github.com/go-gitea/gitea/issues/25498).

- `su git` to become the git user.

- `cd ~` to go to the home directory, which is the `/data/git` directory (which should be mounted to the host).

- Run the the gitea command line from inside the original container to export the data:
`gitea dump-repo --clone_addr <https address of repo> --git_service gitea`


This should create a directory called `data` under the `/data/git` directory, which contains the exported items as a set of YAML files. This directory should be visible on the host, as Gitea mounts the `/data` directory.

In the docker container of the new instance of Gitea, follow the above steps, except use the following command line to import the items.

`gitea restore-repo --repo_name <repo name> --repo_dir pwd/data --owner_name <gitea account name>`

The owner must already be defined in Gitea, but the repo will be created by `restore-repo`.

### What about docker export ?

Exporting the docker container (e.g. `docker export`) would also work, but I wanted to upgrade the version of Gitea, and, as mentioned above, simply copying the mounted volume directory didn’t work.
