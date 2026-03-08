from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase


class HelpPageEditTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="help-editor",
            email="help-editor@example.com",
            password="password",
        )
        self.client.force_login(self.user)

        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.help_file_path = Path(self.temp_dir.name) / "HILFE.md"

    def test_help_page_shows_edit_link(self):
        self.help_file_path.write_text("# Hilfe\n\nStartinhalt", encoding="utf-8")

        with patch("dashboard.views.HELP_FILE_PATH", self.help_file_path):
            response = self.client.get("/hilfe/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bearbeiten")
        self.assertContains(response, "Startinhalt")

    def test_help_page_edit_mode_shows_textarea(self):
        self.help_file_path.write_text("# Hilfe\n\nEditierbar", encoding="utf-8")

        with patch("dashboard.views.HELP_FILE_PATH", self.help_file_path):
            response = self.client.get("/hilfe/?edit=1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Speichern")
        self.assertContains(response, "textarea")
        self.assertContains(response, "Editierbar")

    def test_help_page_post_updates_file_and_shows_notice(self):
        self.help_file_path.write_text("# Hilfe\n\nAlt", encoding="utf-8")

        with patch("dashboard.views.HELP_FILE_PATH", self.help_file_path):
            post_response = self.client.post(
                "/hilfe/",
                data={"markdown_content": "# Hilfe\n\nNeu gespeichert"},
            )
            get_response = self.client.get("/hilfe/?saved=1")

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response["Location"], "/hilfe/?saved=1")
        self.assertEqual(self.help_file_path.read_text(encoding="utf-8"), "# Hilfe\n\nNeu gespeichert")
        self.assertContains(get_response, "Hilfedatei wurde gespeichert.")
        self.assertContains(get_response, "Neu gespeichert")
