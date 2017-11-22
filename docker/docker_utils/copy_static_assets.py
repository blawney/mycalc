import sys
import os
import subprocess
from django.conf import settings

def make_call(command):
        process = subprocess.Popen(command, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
                print 'problem with copying static files!'
                sys.exit(1)

static_bucket = settings.STATIC_FILES_BUCKET

command = 'gsutil -m cp -R static gs://%s/' % static_bucket
make_call(command)

# set public read on those resources:
command = 'gsutil -m acl ch -R -u AllUsers:R gs://%s' % static_bucket
make_call(command)
