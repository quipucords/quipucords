Vagrant.configure("2") do |config|
  # unnoficial RHEL images
  (6..9).each do |n|
    config.vm.define "rhel%d" % n do |vmconfig|
      vmconfig.vm.box = "generic/rhel%d" % n
    end
  end
  # unnoficial centos stream images (for testing purposes we can consider them RHEL-like)
  (8..9).each do |n|
    config.vm.define "stream%d" % n do |vmconfig|
      # we could use the official "centos/stream%d" images, but I'm unable to boot stream9 :'(
      vmconfig.vm.box = "generic/centos%ds" % n
    end
  end
  # allow ssh'ing with password authentication (username and password is "vagrant")
  config.vm.provision "shell", inline: <<-EOF
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
    # fallback to service for systems that don't use systemd
    systemctl restart sshd.service || service sshd restart
  EOF
end
