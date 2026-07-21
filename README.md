# Locust Cluster Automation with Ansible

Cluster Locust terpusat dari VM master. Worker baru cukup ditambahkan ke inventory, kemudian jalankan playbook workers.

Download
```bash
git clone https://github.com/ica4me/locust-ansible-cluster.git /opt/locust-ansible-cluster
```

## 1. Persyaratan

- Control/master: Ubuntu 22.04+ dan dapat SSH ke semua worker.
- Worker: Ubuntu 22.04/24.04 baru, Python 3 tersedia, SSH root/key tersedia.
- DNS dan HTTPS lima domain target dapat diakses dari semua node.

## 2. Bootstrap control node

```bash
cd /opt
# salin proyek ini menjadi /opt/locust-ansible-cluster
cd /opt/locust-ansible-cluster
./scripts/bootstrap-master.sh
```

## 3. SSH tanpa password

```bash
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N ''
ssh-copy-id root@172.16.1.42
ssh-copy-id root@172.16.1.43
ssh-copy-id root@172.16.1.44
```

## 4. Tambah/hapus worker

Edit `inventories/prod/hosts.yml`:

```yaml
locust_workers:
  hosts:
    locust-worker-04:
      ansible_host: 172.16.1.45
```

Lalu:

```bash
ansible all -m ping
ansible-playbook playbooks/workers.yml --limit locust-worker-04
```

## 5. Deploy seluruh cluster

```bash
./scripts/cluster-deploy.sh
```

Web UI:

```text
http://172.16.1.41:8089
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
locust_worker_reserved_cpu_cores: 0
```

Lalu jalankan ulang:

```bash
ansible-playbook playbooks/workers.yml
```

## 7. Operasi harian

```bash
./scripts/cluster-status.sh
./scripts/cluster-restart.sh
ansible locust_workers -a 'free -h'
ansible locust_workers -a 'swapon --show'
ansible locust_workers -a "systemctl list-units 'locust-worker@*.service' --state=running --no-legend"
```

## 8. Scale-up aman

Tambahkan worker ke inventory, pastikan SSH key, lalu:

```bash
ansible-playbook playbooks/workers.yml --limit locust-worker-04
```

Master dengan rebalancing akan menerima worker baru. Untuk benchmark yang auditabel, lebih baik menambah worker sebelum test dimulai.

## 9. Uji bertahap

- 5.000 users, 100/s, 10m
- 10.000 users, 150/s, 20m
- 15.000 users, 180/s, 30m
- 20.000 users, 200-240/s, 30m

Naikkan hanya bila worker tidak missing, CPU generator <85%, dan failures <1%.
