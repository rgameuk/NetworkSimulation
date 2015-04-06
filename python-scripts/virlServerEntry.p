#cloud-config
hostname: virl-sim-server
runcmd:
- start ttyS0
- systemctl start getty@ttyS0.service
- ifconfig eth1 up 10.254.0.36 netmask 255.255.255.0
- sed -i '1 i 127.0.0.1 virl-sim-server' /etc/hosts
- sed -i '/^\s*PasswordAuthentication\s\+no/d' /etc/ssh/sshd_config
- service ssh restart
- service sshd restart
users:
- default
- gecos: User configured by VIRL Configuration Engine 0.10.10
  lock-passwd: false
  name: cisco
  plain-text-passwd: cisco
  shell: /bin/bash
  ssh-authorized-keys:
  - VIRL-USER-SSH-PUBLIC-KEY
  - ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAkZj/7NygpIng1Sw/+Pd1yM6fjyfHNp9fnZ3UvJPATkFrm8+w5TynYuz/uNk4G0pR/ffT9SLMbvUXKbyJQqlsTCx9PwwFB92AY6BZTOfa9Zy/J4F19tCBMoIaGf7YmJVFLSTkiSrmxPMqlWsDD6rx3b70MLihkCDcvmzHTeDNT2WGkwTjqfUJyZ7PMvgwhU80QmB3z3H/JikWWDZWUQiT7kf/7nSCG1MOWILm6Gj1Grxe4ek0+PzO8zyLhKr1TYIqoawO0HiMVb13NTBOJIMQ0T0T8uh1wphjXPdLzPXQ25iUs1sRF+9R8ZPg3CT46Wx//YmxdwodHTxW7bShq1sKJw==
    rsa-key-20150211
  sudo: ALL=(ALL) ALL
- gecos: User configured by VIRL Configuration Engine 0.10.10
  lock-passwd: false
  name: cisco
  plain-text-passwd: cisco
  shell: /bin/bash
  ssh-authorized-keys:
  - VIRL-USER-SSH-PUBLIC-KEY
  - ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAkZj/7NygpIng1Sw/+Pd1yM6fjyfHNp9fnZ3UvJPATkFrm8+w5TynYuz/uNk4G0pR/ffT9SLMbvUXKbyJQqlsTCx9PwwFB92AY6BZTOfa9Zy/J4F19tCBMoIaGf7YmJVFLSTkiSrmxPMqlWsDD6rx3b70MLihkCDcvmzHTeDNT2WGkwTjqfUJyZ7PMvgwhU80QmB3z3H/JikWWDZWUQiT7kf/7nSCG1MOWILm6Gj1Grxe4ek0+PzO8zyLhKr1TYIqoawO0HiMVb13NTBOJIMQ0T0T8uh1wphjXPdLzPXQ25iUs1sRF+9R8ZPg3CT46Wx//YmxdwodHTxW7bShq1sKJw==
    rsa-key-20150211
  sudo: ALL=(ALL) ALL
write_files:
- path: /etc/init/ttyS0.conf
  owner: root:root
  content: |
    # ttyS0 - getty
    # This service maintains a getty on ttyS0 from the point the system is
    # started until it is shut down again.
    start on stopped rc or RUNLEVEL=[12345]
    stop on runlevel [!12345]
    respawn
    exec /sbin/getty -L 115200 ttyS0 vt102
  permissions: '0644'
- path: /etc/systemd/system/dhclient@.service
  content: |
    [Unit]
    Description=Run dhclient on %i interface
    After=network.target
    [Service]
    Type=oneshot
    ExecStart=/sbin/dhclient %i -pf /var/run/dhclient.%i.pid -lf /var/lib/dhclient/dhclient.%i.lease
    RemainAfterExit=yes
  owner: root:root
  permissions: '0644'
