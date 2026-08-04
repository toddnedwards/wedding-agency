from django.db import migrations, models
from django.utils.text import slugify


def populate_vendor_slugs(apps, schema_editor):
    Vendor = apps.get_model('vendors', 'Vendor')

    for vendor in Vendor.objects.all().order_by('id'):
        if vendor.slug:
            continue

        source_name = (vendor.act_name or '').strip() or (vendor.stage_name or '').strip() or (vendor.business_name or '').strip()
        base_slug = slugify(source_name) or 'vendor'
        candidate = base_slug
        counter = 2

        while Vendor.objects.filter(slug=candidate).exclude(pk=vendor.pk).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1

        vendor.slug = candidate
        vendor.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0005_musician_sample_setlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.RunPython(populate_vendor_slugs, migrations.RunPython.noop),
    ]
