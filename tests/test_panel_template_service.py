from app.services.panel_template_service import PanelTemplateService


class DummyNormalizer:
    def normalize_lab_name(self, name: str) -> str:
        return name


def test_get_available_panels_not_empty():
    service = PanelTemplateService()

    panels = service.get_available_panels()

    assert len(panels) > 0
    assert any(panel["panel_name"] == "CBC_Panel" for panel in panels)


def test_get_cbc_template():
    service = PanelTemplateService()

    template = service.get_template("CBC_Panel")

    assert template is not None
    assert template["panel_name"] == "CBC_Panel"
    assert template["display_name"] == "Complete Blood Count (CBC)"


def test_get_required_test_names_for_cbc():
    service = PanelTemplateService()

    required_tests = service.get_required_test_names("CBC_Panel")

    assert required_tests == ["Hemoglobin", "WBC", "Platelets"]


def test_missing_required_labs_for_cbc():
    service = PanelTemplateService()

    missing = service.find_missing_required_labs(
        "CBC_Panel",
        ["Hemoglobin", "WBC"],
        DummyNormalizer(),
    )

    assert missing == ["Platelets"]


def test_no_missing_required_labs_for_cbc():
    service = PanelTemplateService()

    missing = service.find_missing_required_labs(
        "CBC_Panel",
        ["Hemoglobin", "WBC", "Platelets"],
        DummyNormalizer(),
    )

    assert missing == []


def test_unknown_panel_returns_none():
    service = PanelTemplateService()

    template = service.get_template("Unknown_Panel")

    assert template is None