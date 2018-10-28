# Generated by Django 2.1.2 on 2018-10-28 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pca', '0003_section_activity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.TextField()),
            ],
        ),
        migrations.RenameField(
            model_name='course',
            old_name='course_code',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='section',
            old_name='section_code',
            new_name='code',
        ),
        migrations.AddField(
            model_name='registration',
            name='phone',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='section',
            name='is_open',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='section',
            name='meeting_times',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='section',
            name='instructors',
            field=models.ManyToManyField(to='pca.Instructor'),
        ),
        migrations.AlterUniqueTogether(
            name='section',
            unique_together={('code', 'course')},
        ),
    ]
