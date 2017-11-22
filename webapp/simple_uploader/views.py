# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

import datetime
import os
import glob
from google.cloud import storage
import sys
sys.path.append(settings.BACKEND_SRC)

from forms import UploadFileForm

import batch_process

MODELS_DIR = settings.MODELS_DIR
MODEL_SUFFIX = settings.MODEL_SUFFIX
CUSTOM_MODELS_DIR = settings.CUSTOM_MODELS_DIR

from django.contrib.auth.decorators import login_required

def handle_file(f, modelfile):
	now = datetime.datetime.now().strftime('%d%m%y_%H%M%S')
	uploaded_filepath = os.path.join(settings.UPLOAD_DIR, now + '.txt')
	with(open(uploaded_filepath, 'wb+')) as destination:
		for chunk in f.chunks():
			destination.write(chunk)
	result = batch_process.process_batch(uploaded_filepath, modelfile)
	output_fn = now + '.csv'
	output = os.path.join(settings.TEMP_DIR, output_fn)
	result.to_csv(output, sep=',', index=False)
	storage_client = storage.Client()
	bucket = storage_client.get_bucket(settings.DEFAULT_BUCKET)
	blob = bucket.blob(output_fn)
	blob.upload_from_file(open(output), content_type='text/plain')
	return result, blob

@login_required
def process_batch(request):
	if request.method == 'POST':
		linked_model = request.session.get('modelfile', None)
		modelfile = os.path.join(CUSTOM_MODELS_DIR, linked_model)
		dataframe, blob = handle_file(request.FILES['upfile'], modelfile)
		acl = blob.acl
		entity = acl.all().grant_read()
		#entity = acl.user(request.user.email)
		#entity.grant_read()
		acl.save()
		result_link = blob.public_url
		dataframe_as_html = dataframe.to_html(index_names=False, classes=['table','table-striped'])
		total_html = '<a href="%s">Download results</a>' % result_link
		total_html += dataframe_as_html
	return JsonResponse({'result_html':total_html})
