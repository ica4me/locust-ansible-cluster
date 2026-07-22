# Locust Cluster Automation with Ansible

Cluster Locust terpusat dari VM master. Worker baru cukup ditambahkan ke inventory, kemudian jalankan playbook workers.

## 1. Persyaratan

- Control/master: Ubuntu 22.04+ dan dapat SSH ke semua worker.
- Worker: Ubuntu 22.04/24.04 baru, Python 3 tersedia, SSH root/key tersedia.
- DNS dan HTTPS lima domain target dapat diakses dari semua node.
- Rekomendasi Flavor VM (16vCPU 32Gb RAM) x 4 VM Worker

## 2. Bootstrap control node

Download
```bash
git clone https://github.com/ica4me/locust-ansible-cluster.git /opt/locust-ansible-cluster
```

```bash
cd /opt/locust-ansible-cluster
```

Edit dan sesuaikan isi file locustfile.py
Terutama bagian "class SingleEndpointUser(FastHttpUser)"
```bash
nano files/locustfile.py
roles/common/files/locustfile.py

# Sesuaikan bagian Endpoint dan lainya
host = "http://fasthttp.poc.dcloud.biz.id:8080"
```
Ubah inventories/prod/group_vars/all.yml
```bash
nano inventories/prod/group_vars/all.yml
# locust_target_host: "http://fasthttp.poc.dcloud.biz.id:8080"
```
Sesuaikan roles/master/templates/locust-master.service.j2
```bash
nano roles/master/templates/locust-master.service.j2
# --host http://fasthttp.poc.dcloud.biz.id:8080
```
```bash
[Unit]
Description=Locust Distributed Master
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory={{ locust_home }}
ExecStart={{ locust_venv }}/bin/locust \
  -f {{ locust_home }}/locustfile.py \
  --master \
  --master-bind-host {{ locust_master_host }} \
  --master-bind-port {{ locust_master_port }} \
  --web-host {{ locust_web_host }} \
  --web-port {{ locust_web_port }}{% if locust_enable_rebalancing | bool %} \
  --enable-rebalancing{% endif %} \
  --autostart \
  -u 20000 \
  -r 1000 \
  --run-time 30h \
  --host http://fasthttp.poc.dcloud.biz.id:8080 \
  --loglevel INFO \
  --logfile {{ locust_log_dir }}/master.log
Restart=always
RestartSec=3
LimitNOFILE={{ locust_limit_nofile }}
LimitNPROC={{ locust_limit_nproc }}
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
```

```bash
inventories/prod/hosts.yml

# Sesuaikan IP Bagian HOST
  children:
    locust_master:
      hosts:
        locust-master:
          ansible_host: 10.221.66.80
          ansible_connection: local
    locust_workers:
      hosts:
        locust-worker-01:
          ansible_host: 10.221.66.124
        locust-worker-02:
          ansible_host: 10.221.66.157
        locust-worker-03:
          ansible_host: 10.221.66.107
        locust-worker-04:
          ansible_host: 10.221.66.110
```

Boostrap Control Node Locust
```bash
./scripts/bootstrap-master.sh
```

## 3. SSH tanpa password

```bash
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N ''
ssh-copy-id root@10.221.66.124
ssh-copy-id root@10.221.66.157
ssh-copy-id root@10.221.66.107
ssh-copy-id root@10.221.66.110
# ssh-copy-id root@ip-worker-5
```



## 4. Tambah/hapus worker

Edit `inventories/prod/hosts.yml`:

```yaml
locust_workers:
  hosts:
    locust-worker-05:
      ansible_host: 10.221.66.x
```

Lalu:

```bash
ansible all -m ping
ansible-playbook playbooks/workers.yml --limit locust-worker-05
```

## 5. Deploy seluruh cluster

```bash
./scripts/cluster-deploy.sh
```

Web UI:

```text
# http://ip-control-node:8089
http://10.221.66.80:8089
```

## 6. Rumus jumlah proses worker

```text
CPU limit    = vCPU - reserved_cpu_cores
Memory limit = (RAM_MB - reserved_memory_mb) / memory_per_process_mb
Processes    = min(CPU limit, Memory limit, process cap)
```

Default aman:

- reserved CPU: 1 core
- reserved RAM: 2 GB
- estimasi RAM/proses: 768 MB
- swap: 2 GB

Contoh 8 vCPU / 16 GB menghasilkan 7 proses worker. Untuk memakai seluruh 8 core, ubah:

```yaml
# inventories/prod/group_vars/all.yml
locust_worker_reserved_cpu_cores: 0
```

Lalu jalankan ulang:

```bash
ansible-playbook playbooks/workers.yml
```

## 7. Operasi harian

Periksa status cluster
```bash
./scripts/cluster-status.sh
```
Periksa resource
```bash
ansible locust_workers -a 'nproc'
ansible locust_workers -a 'free -h'
ansible locust_workers -a 'swapon --show'
ansible locust_workers -a "systemctl list-units 'locust-worker@*.service' --state=running --no-legend"
```
Restart seluruh cluster sekaligus
```bash
./scripts/cluster-restart.sh
```

## 8. Scale-up aman

Tambahkan worker ke inventory, pastikan SSH key, lalu:

```bash
ansible-playbook playbooks/workers.yml --limit locust-worker-05
```

Master dengan rebalancing akan menerima worker baru. Untuk benchmark yang auditabel, lebih baik menambah worker sebelum test dimulai.

## 9. Uji bertahap

- 5.000 users, 100/s, 10m
- 10.000 users, 150/s, 20m
- 15.000 users, 180/s, 30m
- 20.000 users, 200-240/s, 30m

**Naikkan hanya bila worker tidak missing, CPU generator <85%, dan failures <1%.**

---
## Install Ansible
```bash
sudo apt update
sudo apt install -y software-properties-common unzip openssh-client
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible
ansible --version
```
