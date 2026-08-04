from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0004_vendorprofileupdaterequest_vendorprofilevideodraft_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='musician',
            name='sample_setlist',
            field=models.TextField(blank=True),
        ),
    ]
