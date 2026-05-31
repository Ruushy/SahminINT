from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recon', '0002_techresult_server_software_emailresult_portscan_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PortScan',
        ),
    ]
