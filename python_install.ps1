#Set-ExecutionPolicy RemoteSigned

$notwget = New-Object System.Net.WebClient

# Download and install Python 2.7
$notwget.DownloadFile("http://www.python.org/ftp/python/2.7.6/python-2.7.6.amd64.msi", "D:\python-2.7.6.amd64.msi")

# Run the installer in non-interactive installation mode
& msiexec /a "D:\python-2.7.6.amd64.msi" ALLUSERS=1

# Install the latest and greatest version of Setuptools
$notwget.DownloadFile("https://bootstrap.pypa.io/ez_setup.py", "D:\ez_setup.py")
# Rather than muck with PATH and PYTHONPATH, simply did these installs directly
& "C:\Python27\python.exe" D:\ez_setup.py

#Get the pip
$notwget.DownloadFile("https://bootstrap.pypa.io/get-pip.py", "D:\get-pip.py")
& "C:\Python27\python.exe" D:\get-pip.py

