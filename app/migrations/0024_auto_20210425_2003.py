# Generated by Django 3.1.7 on 2021-04-26 00:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0023_bookmarkchallenge'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='upvoteCount',
            new_name='upvotes',
        ),
        migrations.AddField(
            model_name='challenge',
            name='upvotes',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='project',
            name='upvotes',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='UpvoteProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('obj', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.project', verbose_name='Project')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 'upvote_project',
            },
        ),
        migrations.CreateModel(
            name='UpvoteComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('obj', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.comment', verbose_name='Comment')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 'upvote_comment',
            },
        ),
        migrations.CreateModel(
            name='UpvoteChallenge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('obj', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.challenge', verbose_name='Challenge')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 'upvote_challenge',
            },
        ),
    ]
