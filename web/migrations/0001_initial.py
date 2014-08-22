# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Job'
        db.create_table(u'web_job', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('script', self.gf('django.db.models.fields.TextField')()),
            ('log', self.gf('django.db.models.fields.TextField')()),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'web', ['Job'])


    def backwards(self, orm):
        # Deleting model 'Job'
        db.delete_table(u'web_job')


    models = {
        u'web.job': {
            'Meta': {'object_name': 'Job'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {}),
            'script': ('django.db.models.fields.TextField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        }
    }

    complete_apps = ['web']