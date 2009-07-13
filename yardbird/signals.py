#!/usr/bin/python

from django.dispatch import Signal

request_started = Signal(providing_args=["request"])
request_finished = Signal(providing_args=["request", "response"])
