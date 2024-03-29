# pylint: disable=no-member
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import django

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from .models import DataPointType

@login_required
def pdk_codebook_page(request, generator):
    data_type = get_object_or_404(DataPointType, generator=generator)

    context = {
        'data_type': data_type,
        'data_types': DataPointType.objects.exclude(first_seen=None).order_by('generator')
    }

    if django.VERSION[0] < 3:
        return render(request, 'pdk_codebook_page_lts11.html', context=context)

    return render(request, 'pdk_codebook_page.html', context=context)

@login_required
def pdk_codebook_sitemap(request): # pylint: disable=unused-argument
    return HttpResponse(json.dumps({}, indent=2), content_type='application/json', status=200)

def pdk_codebook_page_start(request): # pylint: disable=unused-argument
    first_type = DataPointType.objects.all().order_by('generator').first()

    return redirect(first_type)
