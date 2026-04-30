from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
import io

from apps.accounts.models import User
from apps.core.models import SocialClub
from apps.members.models import Profile


def _png_bytes(color=(120, 160, 200)):
    stream = io.BytesIO()
    Image.new("RGB", (4, 4), color).save(stream, format="PNG")
    return stream.getvalue()


@pytest.mark.django_db
def test_social_club_admin_can_upload_profile_banner_and_gallery_images(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    club = SocialClub.objects.create(
        name="CSC Media Club",
        email="media@example.com",
        street_address="Media 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123",
        is_active=True,
        is_approved=True,
    )
    admin = User.objects.create_user(
        email="media-admin@example.com",
        password="StrongPass123!",
        first_name="Media",
        last_name="Admin",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    Profile.objects.create(
        user=admin,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=550001,
        monthly_counter_key="2026-04",
    )

    client.force_login(admin)
    response = client.post(
        reverse("core:social_club_profile"),
        data={
            "name": club.name,
            "public_description": "Wir zeigen unsere Clubraeume und Events.",
            "email": club.email,
            "support_email": "",
            "membership_email": "",
            "prevention_email": "",
            "finance_email": "",
            "privacy_contact": "",
            "data_protection_officer": "",
            "phone": club.phone,
            "website": "",
            "street_address": club.street_address,
            "postal_code": club.postal_code,
            "city": club.city,
            "board_representatives": "",
            "register_entry": "",
            "register_court": "",
            "tax_number": "",
            "vat_id": "",
            "supervisory_authority": "",
            "content_responsible": "",
            "responsible_person": "",
            "language_notice": "",
            "legal_basis_notice": "",
            "retention_notice": "",
            "external_services_text": "",
            "prevention_officer_name": "",
            "prevention_notice": "",
            "instagram_url": "",
            "telegram_url": "",
            "whatsapp_url": "",
            "profile_image": SimpleUploadedFile("logo.png", _png_bytes((255, 0, 0)), content_type="image/png"),
            "banner_image": SimpleUploadedFile("banner.png", _png_bytes((0, 255, 0)), content_type="image/png"),
            "gallery_image_1": SimpleUploadedFile("g1.png", _png_bytes((0, 0, 255)), content_type="image/png"),
            "gallery_image_2": SimpleUploadedFile("g2.png", _png_bytes((50, 50, 50)), content_type="image/png"),
            "gallery_image_3": SimpleUploadedFile("g3.png", _png_bytes((90, 90, 90)), content_type="image/png"),
            "gallery_image_4": SimpleUploadedFile("g4.png", _png_bytes((120, 120, 120)), content_type="image/png"),
            "gallery_image_5": SimpleUploadedFile("g5.png", _png_bytes((200, 200, 200)), content_type="image/png"),
        },
        follow=True,
    )

    assert response.status_code == 200
    club.refresh_from_db()
    assert club.profile_image.name
    assert club.banner_image.name
    assert club.gallery_image_1.name
    assert club.gallery_image_5.name

    public_response = client.get(reverse("core:social_club_public_detail", args=[club.slug]))
    public_html = public_response.content.decode("utf-8")
    assert public_response.status_code == 200
    assert club.profile_image.url in public_html
    assert club.banner_image.url in public_html
    assert club.gallery_image_1.url in public_html
