---
title: "Experimenting with Kubernetes"
pubDate: 2024-11-24
updatedDate: 2024-12-09
description: "Setting up a Kubernetes cluster is a rewarding way to deepen your understanding of container orchestration. For those exploring Kubernetes for the first time…"
---
Setting up a Kubernetes cluster is a rewarding way to deepen your understanding of container orchestration. For those exploring Kubernetes for the first time or looking to experiment in a controlled environment, using [Kind](https://kind.sigs.k8s.io) (Kubernetes IN Docker) offers a straightforward and lightweight solution. Kind allows you to create Kubernetes clusters within Docker containers, making it ideal for homelabs, local testing, and experimentation.

In this guide, we’ll walk through the process of setting up a Kubernetes cluster using Kind. This approach keeps the complexity low while providing a fully functional cluster you can use to explore Kubernetes concepts. By the end of the article, you’ll have your own local Kubernetes environment up and running, ready for experimentation and learning.

For an overview of Kubernetes, I learned a lot from the book “Kuberentes in a Month of Lunches” from Manning Publications.. If you’re new to Kind, their [official documentation](https://kind.sigs.k8s.io) is a great resource for understanding how it works and its capabilities.

A [github](https://github.com/icosahedron/kubernetes-homelab) repository is available that contains all the code necessary to create and use the cluster described here. Since the github repo will be updated as as I learn more, each step in the cluster development is tagged.

### Directory Structure

The github repository contains the following directory structure:

- ./helm - contains subdirectories, one for each application.

- ./yaml - contains manifests that aren’t provided as Helm charts.

- ./storage - directory used for storage for the applications in the cluster. Each app has its own subdirectory.

## Install a Container Runtime and Kind

This guide is written using Docker, but it should be possible using Podman or perhaps even containerd. Where it says Docker, you can substitute your container runtime of choice.

For this guide’s purposes, I’ve provisioned a separate Ubuntu 22.04 VM in Hyper-V on Windows and the same using OrbStack on macOS. Each VM has Docker installed.

Kind is available through most package managers and also via [Homebrew](/148786cfa01080099a95c14fb94e99f1?pvs=25) for macOS or Linux. Instructions for installing are available on the [Kind website](https://kind.sigs.k8s.io).

## Install Kubernetes Tools

There are several utilities necessary to provision and manage a Kubernetes cluster. The ones we’ll be using for our experiment are:

- Helm - package manager for Kubernetes. Builds manifests (yaml files) from templates.

- Kubectl - primary method for interacting with a cluster.

- Kapp - a package manager that provides dependency aware installation of resources and reports on their progress during installation

- k9s - terminal based cluster information. Allows seeing status of resources and logs, and connects to pods with a shell

There are lots of other tools available, but for this article, we stick with ones available for use in the terminal.

## Configure and Start the Kind Cluster

Kind clusters are configured with their own YAML file.

Our version will have one control plane and two worker nodes.

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
featureGates:
  "StatefulSetAutoDeletePVC": true
name: homelab
nodes:
  - role: control-plane
    image: kindest/node:v1.31.0@sha256:53df588e04085fd41ae12de0c3fe4c72f7013bba32a20e7325357a1ac94ba865
    labels:
      ingress-ready: true
    extraPortMappings:
    - containerPort: 80
      hostPort: 8080
      protocol: TCP
  - role: worker
    image: kindest/node:v1.31.0@sha256:53df588e04085fd41ae12de0c3fe4c72f7013bba32a20e7325357a1ac94ba865
    extraMounts:
      - hostPath: ./storage
        containerPath: /storage
    labels:
      storage: high-capacity
      role: database
  - role: worker
    image: kindest/node:v1.31.0@sha256:53df588e04085fd41ae12de0c3fe4c72f7013bba32a20e7325357a1ac94ba865
    labels:
      cpu: high-capacity
    extraMounts:
      - hostPath: ./storage
        containerPath: /storage
```

Not everything in this file need explanation at this point, but here are the highlights:

- Each `node` has a `role`, either *control-plane* or *worker*. It is possible to have multiple control planes in a cluster for redundancy, but one suffices for this cluster.

- `image` is the container image that is used. This is a [special container image](https://kind.sigs.k8s.io/docs/design/node-image/) specifically for kind that contains systemd and allows running pods (containers) within the node containers.

- `labels` are tags that identify which nodes should be used for certain applications or have certain capabilities. In this config, the control plane will also house the ingress controller. One node is marked as having a lot of storage available, and the other is marked as being compute capable.

- `extraMounts` maps a directory on the host to a directory in each node, not unlike the `-v` option in the Docker CLI. In this config, the subdirectory `storage` is mapped to the directory `/storage` in the node container.

- `extraPortMappings` maps ports from the host to the node. As explained further below, this maps port 8080 of the host to port 443 of the container node on the control plane..

To start the cluster, the command `kind create cluster --config yaml/config.kind.yaml`. It should look as below.

:::embed{url="https://icosahedron.github.io/notion-widgets/"}
:::

## Install NFS for Persistent Volumes

There are many ways to store data in a cluster, but the simplest is probably NFS. For convenience, the NFS server used is installed in the cluster.

Also installed is the Container Storage Interface (CSI) interface for NFS. CSI is a plugin API that allows various storage systems to provide space for persistent volume claims.

These commands can be found in the `justfile` in the above mentioned github repo.

```shell
helm template nfs-server helm/nfs-server --namespace default --set architecture=$(uname -m) > nfs-server-helm.yaml                                                                                  │
kapp deploy --app nfs-server -f nfs-server-helm.yaml -y                                                                                                                                             │
helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts                                                                                          │
helm template csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system --version v4.9.0 > nfs-csi-driver-helm.yaml                                                                      │
kapp deploy --app csi-driver-nfs -f nfs-csi-driver-helm.yaml -y                                                                                                                                     │
```

This installs the NFS server and the CSI driver that can use the NFS server. Our first application deployment below will show how this is used to provide storage to an application though a Persistent Volume and Persistent Volume Claim.

:::callout{icon="💡"}

 We use `helm` to create the template, and then use `kapp` to perform the  installation with the resulting manifest. Kapp provides resource dependency resolution and will wait for all the resources to become available before reporting success.

:::

The playback below shows `kapp` and how it waits for each resource to become available.

:::embed{url="https://icosahedron.github.io/notion-widgets/install-nfs-server.html"}
:::

## Install Ingress Controller

There are also several ways to get traffic into a cluster. For HTTP traffic, a common way is to use an ingress controller. An ingress controller acts as a reverse proxy, with rules on how to route traffic based on the host name and other rules.

The Nginx ingress controller is popular and well documented, so we’ll use that one.

To install it, these commands pull the manifest directly from Github into the cluster, rather than using a local helm chart and kapp.

```shell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl rollout status deployment ingress-nginx-controller -n ingress-nginx
```

:::embed{url="https://icosahedron.github.io/notion-widgets/install-ingress.html"}
:::

The ingress controller will accept traffic on the node it’s installed in. Which node the ingress is installed on is determined by the label “ingress-ready: true”. Which the control-plane node in the cluster config above has applied.

## Redirect HTTP Traffic

Since the cluster is within docker containers on a single computer, either VM or host, and the http port is a privileged port, the cluster can’t receive traffic on port 80 by default. Further configuration is required to allow traffic on port 80 to reach the cluster.

There are a [number of ways](https://linuxconfig.org/how-to-bind-a-rootless-container-to-a-privileged-port-on-linux) to make port 80 available to non-privileged processes, but this cluster will use [`redir`](https://github.com/troglobit/redir). A systemd service that runs `redir` will do nicely. Save the TOML block below into `/etc/systemd/system/redir.service` and start it with `sudo systemctl enable --now redir.service`.

```toml
[Unit]
Description=Redirect tcp port 80 to 8080 with redir

[Service]
ExecStart=/bin/redir -sn :80 127.0.0.1:8080

[Install]
WantedBy=multi-user.target
```

We partially accounted for this when we created the cluster configuration that listens on port 8080. Traffic comes in to port 80, is forwarded to the ingress node on port 8080, and then the node forwards that to the ingress controller on its port 80.



## Install Web Server for Testing

Now to install something to demonstrate that all this is working. Why not another Nginx web server?

This will tie together everything and show that our cluster is in a proper state to host applications.

The storage for files for the web server to read will be in the `./storage/nginx` directory.

The entire helm chart is hosted in the github repo for this article, but here are a few of the templates.

The first template to look at is the Persistent Volume. 

```toml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nginx-nfs
  namespace: {{ .Values.namespace }}
spec:
  capacity:
    storage: {{ .Values.storage.size }}
  accessModes:
    - ReadOnlyMany
  mountOptions:
    - nfsvers=4.1
  csi:
    driver: nfs.csi.k8s.io
    # volumeHandle format: {nfs-server-address}#{sub-dir-name}#{share-name}
    # make sure this value is unique for every share in the cluster
    volumeHandle: {{ .Values.storage.nfs.server }}#{{ .Values.storage.nfs.path }}#nginx
    volumeAttributes:
      server: {{ .Values.storage.nfs.server }}
      share: {{ .Values.storage.nfs.path }}
```

Here is an example of using the NFS server installed earlier. The `csi` section shows the driver and the server, share combination that should be used for the persistent volume. These are configured in the `values.yaml`.

To use this storage requires a Persistent Volume Claim (PVC). Kubernetes will match the claim with the available volumes. To match them, the PVC needs to match the PV on the *accessMode* and *volumeName*. It would also match on the *storageClassName* if that were not empty and the PV had defined one as well. And the size in the PV must at be at least as large as the requested storage size in the PVC.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nginx
  namespace: {{ .Values.namespace }}
spec:
  accessModes:
    - ReadOnlyMany
  storageClassName: ""
  resources:
    requests:
      storage: {{ .Values.storage.size }}
  volumeName: nginx-{{ .Values.storage.pv }}
```

The deployment sets up 2 instances of the web server, so the PV has a `ReadWriteMany` access mode. (The instance count really should be a setting in the values file.)

Installation is similar to every other component, and the commands are in the `justfile` within the repo. The Nginx web server can be installed with `just deploy-nginx`.

## Test the Cluster

We have the cluster set up and appropriate infrastructure along with a web server installed. Test it with a simple index.html file place in the `./storage/nginx` directory.

```yaml
<html>
<head>
</head>
<body>Hello, world</body>
</html>
```

Followed by a simple test to verify that the web servers in the cluster can be reached from outside the cluster.

```shell
curl http://localhost
```

:::embed{url="https://icosahedron.github.io/notion-widgets/curl-test.html"}
:::

## Next Steps

With this much done, the cluster is ready for more applications, and more articles on how to extend this experiment. Some things I can think of:

- [ ] HTTPS and certificates

- [ ] Database

- [ ] Source control

- [ ] CI/CD

- [ ] E-book/PDF inventory

- [ ] Observability of Cluster

- [ ] Analytics for Blog
