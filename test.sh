#!/bin/bash
PYTHONPATH=.:$PYTHONPATH django-admin.py test subforms --settings=test_settings

