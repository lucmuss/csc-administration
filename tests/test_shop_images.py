from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings


@pytest.mark.django_db
@override_settings(MEDIA_ROOT=Path("/tmp/csc-test-media"))
def test_shop_displays_strain_image(client, member_user):
    from apps.inventory.models import Strain

    client.force_login(member_user)
    strain = Strain.objects.create(
        name="Orange Bud",
        thc="20.50",
        cbd="0.30",
        price="8.00",
        stock="0.00",
        image=SimpleUploadedFile("orange-bud.jpg", b"fake-image", content_type="image/jpeg"),
    )

    response = client.get("/orders/shop/")

    assert response.status_code == 200
    assert strain.image.url in response.content.decode("utf-8")
