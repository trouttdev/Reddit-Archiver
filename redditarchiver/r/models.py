# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class Comments(models.Model):
    comment_id = models.IntegerField(primary_key=True)
    thread_id = models.IntegerField()
    parent_id = models.IntegerField()
    author = models.CharField(max_length=60)
    comment_text = models.TextField()
    votes = models.IntegerField()
    create_time = models.IntegerField()
    class Meta:
        db_table = u'comments'

class Last(models.Model):
    url = models.CharField(max_length=30)
    class Meta:
        db_table = u'last'

class Reddits(models.Model):
    subreddit_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=768)
    url = models.CharField(max_length=768)
    nsfw = models.IntegerField()
    subscribers = models.IntegerField()
    last_update = models.DateTimeField()
    next_update = models.DateTimeField()
    class Meta:
        db_table = u'reddits'

class ThreadMainText(models.Model):
    thread_id = models.IntegerField(primary_key=True)
    text = models.TextField(blank=True)
    class Meta:
        db_table = u'thread_main_text'

class Threads(models.Model):
    thread_id = models.IntegerField(primary_key=True)
    subreddit_id = models.IntegerField()
    title = models.CharField(max_length=900)
    domain = models.CharField(max_length=225)
    author = models.CharField(max_length=60)
    submit_time = models.IntegerField()
    votes = models.IntegerField()
    comment_count = models.IntegerField()
    thread_link = models.CharField(max_length=525)
    comment_link = models.CharField(max_length=450)
    nsfw = models.IntegerField()
    update_id = models.IntegerField()
    class Meta:
        db_table = u'threads'

class Updates(models.Model):
    update_id = models.IntegerField(primary_key=True)
    subreddit_id = models.IntegerField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'updates'

