# Overview
Quipucords can identify the following cloud providers through a network scan; Amazon, Azure, and Google. The following instructions explain how to set up vms on each of the above clouds and run a scan with quipucords.
- [Amazon](#amazon)
- [Azure](#azure)
- [Google](#google)

# <a name="amazon"></a> Amazon
### Official Documentation:
- [Connection Prerequisites](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connection-prereqs.html)
- [Accessing Instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html)
#### Summarized Instructions:
1. Log in to your amazon account at https://aws.amazon.com/.
2. At the top of the page, click on the Services drop down menu and select `EC2` (underneath Compute).
3. In the left hand navigation bar, select `Instances`, and then click on the `Launch Instance` button.
4. Select the free tier eligible RHEL 8 AMI (leave the default 34-bit (x86)).
5. The default should be the free tier eligible t2.micro - leave this and click the `Review and Launch` button at the bottom of the page.
6. Click `Launch`.
7. In the popup, select `Create a new key pair` and give the key pair a name and click `Download Key Pair`.
8. Click `Launch Instances`.
9. Find the downloaded .pem file on your local machine and change the permissions to `0400`:
```
        chmod 400 /path/my-key-pair.pem
```
10. Now go back to the amazon console and click `View Instances` at the bottom of the page.
11. This menu will show you the IPv4 Public IP of your instance. Copy that.
12. In the terminal check that you can ssh to your machine:
```
        ssh -i ~/.ssh/cloud_provider_key_pair.pem ec2-user@IP
```

13. Once you have successfully connected you can create a cred, source, and scan to use Quipucords to scan your instance:
```
        qpc cred add --name aws --type network --username ec2-user --sshkeyfile /path/my-key-pair.pem
        qpc source add --name aws --type network --cred aws --hosts IP
        qpc scan add --name awsScan --sources aws
        qpc scan start --name awsScan
```

##### ** NOTE: when finished, make sure to stop and/or terminate your VMS

# <a name="azure"></a> Azure
### Official Documentation:
- [Quick create portal](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal)
- [Create ssh keys](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/mac-create-ssh-keys)
#### Summarized Instructions:
1. Log in to your Azure account [here](https://portal.azure.com/#home).
2. On the home page, click on the `Virtual machines` option.
3. Select `Add` in the top left corner and then click `Create VM from Azure MarketPlace`.
4. Select the RHEL 7.6 machine image (you may have to search Red Hat Enterprise Linux in the search bar).
5. Select `Start with a pre-set configuration`.
6. Select `Dev/Test`.
7. Leave the default of `General Purpose (D-Series)`.
8. Under Resource group click `create new`, give the resource group a name and then select it.
9. Then give your virtual machine a name - for example `azure-trial-machine`
10. Create a username such as `aaiken`
11. In a terminal generate an ssh key pair using:
```
        ssh-keygen -t rsa -b 2048
```

12. Save the key pair to a known place and copy the contents of the public key and paste it into the SSH public key text box.
13. Leave the port defaults.
14. At the bottom click `Review + create` and enter your email/phone number.
15. Click `create` at the bottom - this might take a little while but when it is finished click View Resource
16. This page allows you to get your ip address, with which you should check your ssh connection:
```
        ssh -i ~/.ssh/cloud_provider_key_pair your-username@IP
```

17. Once you have successfully connected you can create a cred, source, and scan to use Quipucords to scan your instance:
```
        qpc cred add --name azure --type network --username aaiken --sshkeyfile ~/path/to/private-key:
        qpc source add --name azure --type network --cred azure --hosts IP
        qpc scan add --name azureScan --sources azure
        qpc scan start --name azureScan
```
##### ** NOTE: when finished, make sure to stop and/or terminate your VMS

# <a name="google"></a> Google
1. Follow this [blog](https://www.freecodecamp.org/news/how-to-create-and-connect-to-google-cloud-virtual-machine-with-ssh-81a68b8f74dd/), except choose a RHEL marketplace image.
2. If you have any trouble connecting or see the following error:
```
        Permission denied (publickey,gssapi-keyex,gssapi-with-mic).
```
* You can potentially solve this by creating a fake ssh directory with `700` permissions and move the private key that you generated for your instance to this directory with `600` permissions (as expected). When you ssh to your instance, provide the path to this private key.
3. Once you have successfully connected you can create a cred, source, and scan to use Quipucords to scan your instance:
```
        qpc cred add --name google --type network --username yourUser --sshkeyfile ~/path/to/private-key
        qpc source add --name google --type network --cred google --hosts IP
        qpc scan add --name googleScan --sources google
        qpc scan start --name googleScan

```
##### ** NOTE: when finished, make sure to stop and/or terminate your VMS