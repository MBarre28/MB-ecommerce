terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.6.2"
    }
  }
}

provider "docker" {
  host = "tcp://localhost:2375" # For windows users
}

resource "docker_image" "debian" {
  name = "debian:latest"
}

resource "docker_image" "ansible" {
  name = "alpine/ansible:latest"
}

resource "docker_network" "lab" {
  name = "lab-network"
}

resource "docker_container" "manager" {
  image = docker_image.ansible.image_id
  name  = "manager_node"

  # Install OpenSSH server and Python
  command = [
    "bash", "-c","chown -R root:root /root/.ssh/private_key &&  chmod 600 /root/.ssh/private_key && eval $(ssh-agent) && ssh-add /root/.ssh/private_key && ssh-add -l && sleep infinity"
  ]

 volumes {
    host_path      = abspath("${path.module}/private_key")
    container_path = "/root/.ssh/private_key"
  }
  # Mount SSH keys (use absolute path)
  volumes {
    host_path      = abspath("${path.module}/inventory.ini")
    container_path = "/etc/ansible/hosts"
  }

  volumes {
    host_path      = abspath("${path.module}/ssh_config")
    container_path = "/root/.ssh/config"
  }

  # Connect to the network
  networks_advanced {
    name = docker_network.lab.id
  }
}

resource "docker_container" "worker" {
  count = 3
  image = docker_image.debian.image_id
  name  = "worker_node_${count.index}"
  hostname  = "worker_node_${count.index}"

  # Install OpenSSH server and Python
  command = [
    "bash", "-c", "apt-get update && apt-get install -y openssh-server python3 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && sed -i 's/#IgnoreRhosts yes/IgnoreRhosts yes/' /etc/ssh/sshd_config && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && echo 'AuthorizedKeysFile     /root/.ssh/authorized_keys' >> /etc/ssh/sshd_config && chown -R root:root /root/.ssh && mkdir -p /var/run/sshd && /usr/sbin/sshd -D -E /sshd.log"
  ]

  # Expose port 2222 + index
  ports {
    internal = 22
    external = 2222 + count.index
    protocol  = "tcp"
  }

  # Mount SSH keys (use absolute path)
  volumes {
    host_path      = abspath("${path.module}/authorized_keys")
    container_path = "/root/.ssh/authorized_keys"
  }

  networks_advanced {
    name = docker_network.lab.id
  }
}

# Create authorized keys file for ssh access
resource "null_resource" "ssh_keys" {
  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH2WuypJ/69mNEohtYPh0I7skjVvp+fC42iEan1W34nP DELL LAPTOP@Desktop' > ./authorized_keys" # Use the public key you made before. It should be in ed_2559.pub
  }
}



resource "local_file" "ssh_config" {
  filename = "${path.module}/ssh_config"
  content = <<-EOF
  Host *
    StrictHostKeyChecking no
    IdentityFile /root/.ssh/private_key
    UserKnownHostsFile /dev/null
EOF
}

resource "local_file" "manager_ansible_inventory" {
  filename = "${path.module}/inventory.ini"
  content = <<-EOF
[workers]
${join("\n", [for i in range(length(docker_container.worker)) : "worker_node_${i} ansible_host=worker_node_${i} ansible_port=22 ansible_user=root"])}
EOF
}

# Create Ansible inventory file
resource "local_file" "ansible_inventory" {
  filename = "${path.module}/hosts.ini"
  content = <<-EOF
[workers]
${join("\n", [for i in range(length(docker_container.worker)) : "worker_node_${i} ansible_host=localhost ansible_port=${2222 + i} ansible_user=root"])}
EOF
}
