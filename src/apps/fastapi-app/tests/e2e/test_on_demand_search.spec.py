"""
E2E Test: On-Demand Vehicle Search Feature

Tests the complete flow from frontend SearchForm to backend API to result display.
The SearchForm lives on the /opportunities page.

Features tested:
- SearchForm component with brand/model/year inputs
- POST /api/search/vehicle API endpoint
- Results display with FIPE price and opportunities
- Error handling and loading states
"""
import re
import sqlite3
from pathlib import Path

import pytest
import requests
from playwright.sync_api import Page, expect


_DB_PATH = Path(__file__).parent.parent.parent.parent.parent / "fipe_hunter.db"


def _purge_vehicle(brand: str, model: str, year: int) -> int:
    """
    Remove search_cache + opportunities for a vehicle so the next search is fresh.
    Returns the number of opportunity rows deleted.
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "DELETE FROM search_cache WHERE brand=? AND model=? AND year=?",
        (brand.lower(), model.lower(), year),
    )
    cur = conn.execute(
        "DELETE FROM opportunities WHERE lower(brand) LIKE ? AND lower(model) LIKE ? AND year=?",
        (f"%{brand.lower()}%", f"%{model.lower()}%", year),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


BASE_URL = "http://localhost:3001/opportunities"


@pytest.mark.e2e
class TestOnDemandSearchE2E:
    """E2E tests for on-demand vehicle search feature."""

    def _fill_search_form(self, page: Page, brand: str, model: str, year: str = ""):
        """Helper to fill in the search form fields."""
        page.get_by_placeholder("e.g. Honda", exact=True).fill(brand)
        page.get_by_placeholder("e.g. Civic", exact=True).fill(model)
        if year:
            page.get_by_placeholder("Optional").fill(year)

    def _submit_form(self, page: Page):
        """Helper to click the Search Now button."""
        page.locator('button:has-text("Search Now")').click()

    def test_successful_search_fipe_only(self, page: Page):
        """
        Test successful search that returns FIPE price and OLX results.
        Scenario: Toyota Corolla 2022.
        """
        page.goto(BASE_URL)


        brand_input = page.get_by_placeholder("e.g. Honda", exact=True)
        model_input = page.get_by_placeholder("e.g. Civic", exact=True)
        year_input = page.get_by_placeholder("Optional")
        submit_button = page.locator('button:has-text("Search Now")')

        expect(brand_input).to_be_visible()
        expect(model_input).to_be_visible()
        expect(year_input).to_be_visible()
        expect(submit_button).to_be_visible()


        self._fill_search_form(page, "Toyota", "Corolla", "2022")
        self._submit_form(page)


        expect(page.locator('button:has-text("Searching")')).to_be_visible(timeout=3000)


        expect(page.get_by_text("FIPE Reference Price")).to_be_visible(timeout=15000)


        expect(page.get_by_text("Toyota")).to_be_visible()
        expect(page.get_by_text("Corolla")).to_be_visible()


        expect(page.locator('button:has-text("Search Now")')).to_be_enabled()

    def test_search_with_fipe_error(self, page: Page):
        """
        Test search when FIPE lookup fails but search completes.
        Scenario: Honda Civic 2020 — FIPE not found, shows amber error.
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "Honda", "Civic", "2020")
        self._submit_form(page)


        expect(page.locator('button:has-text("Search Now")')).to_be_enabled(timeout=15000)


        expect(page.get_by_text("FIPE lookup failed")).to_be_visible(timeout=5000)

    def test_form_validation_empty_fields(self, page: Page):
        """
        Test form validation prevents submission with empty required fields.
        """
        page.goto(BASE_URL)

        submit_button = page.locator('button:has-text("Search Now")')
        submit_button.click()


        expect(submit_button).to_be_visible()


        brand_input = page.get_by_placeholder("e.g. Honda", exact=True)
        expect(brand_input).to_have_attribute("required", "")

    def test_form_validation_short_inputs(self, page: Page):
        """
        Test client-side validation for minimum length.
        brand.length < 2 || model.length < 2 → early return, no API call.
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "H", "C")
        self._submit_form(page)


        page.wait_for_timeout(500)
        expect(page.locator('button:has-text("Search Now")')).to_be_visible()


        brand_input = page.get_by_placeholder("e.g. Honda", exact=True)
        expect(brand_input).to_have_attribute("minlength", "2")

    def test_form_validation_invalid_year(self, page: Page):
        """
        Test year range validation (1950-2026).
        isNaN(y) || y < 1950 || y > 2026 → early return.
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "Honda", "Civic", "1900")
        self._submit_form(page)


        page.wait_for_timeout(500)
        expect(page.locator('button:has-text("Search Now")')).to_be_visible()


        year_input = page.get_by_placeholder("Optional")
        expect(year_input).to_have_attribute("min", "1950")
        expect(year_input).to_have_attribute("max", "2026")

    def test_loading_state_indicators(self, page: Page):
        """
        Test loading indicators during API call.
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "Toyota", "Corolla", "2022")
        self._submit_form(page)


        searching_button = page.locator('button:has-text("Searching")')
        expect(searching_button).to_be_visible(timeout=3000)


        expect(searching_button).to_be_disabled()


        expect(page.locator('button svg.animate-spin')).to_be_visible()


        expect(page.locator('button:has-text("Search Now")')).to_be_enabled(timeout=15000)

    def test_error_handling_network_failure(self, page: Page):
        """
        Test error handling when API call fails (network blocked).
        """
        page.goto(BASE_URL)


        page.route("**/api/search/vehicle", lambda route: route.abort())

        self._fill_search_form(page, "Honda", "Civic", "2020")
        self._submit_form(page)


        expect(page.locator('.text-red-600')).to_be_visible(timeout=10000)

    def test_error_handling_vehicle_not_found(self, page: Page):
        """
        Test behavior when searching for a non-existent vehicle.
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "NonExistentBrand", "NonExistentModel", "2000")
        self._submit_form(page)


        expect(page.locator('button:has-text("Search Now")')).to_be_enabled(timeout=15000)


        error_or_result = page.locator('.text-red-600, .text-amber-700, :text("No listings found")')
        expect(error_or_result.first).to_be_visible(timeout=5000)

    def test_input_trimming(self, page: Page):
        """
        Test whitespace trimming (brand.trim() and model.trim()).
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "  Toyota  ", "  Corolla  ", "2022")
        self._submit_form(page)


        expect(page.get_by_text("FIPE Reference Price")).to_be_visible(timeout=15000)
        expect(page.get_by_text("Toyota")).to_be_visible()
        expect(page.get_by_text("Corolla")).to_be_visible()

    def test_year_optional_field(self, page: Page):
        """
        Test that year field is optional.
        """
        page.goto(BASE_URL)


        self._fill_search_form(page, "Honda", "Civic")
        self._submit_form(page)


        expect(page.locator('button:has-text("Searching")')).to_be_visible(timeout=3000)


        expect(page.locator('button:has-text("Search Now")')).to_be_enabled(timeout=15000)

    def test_multiple_searches_consecutively(self, page: Page):
        """
        Test sequential searches with different data.
        """
        page.goto(BASE_URL)


        self._fill_search_form(page, "Toyota", "Corolla", "2022")
        self._submit_form(page)
        expect(page.get_by_text("FIPE Reference Price")).to_be_visible(timeout=15000)
        expect(page.get_by_text("Toyota")).to_be_visible()


        self._fill_search_form(page, "Honda", "Civic", "2020")
        self._submit_form(page)
        expect(page.get_by_text("Honda")).to_be_visible(timeout=15000)
        expect(page.get_by_text("Civic")).to_be_visible()

    def test_responsive_layout(self, page: Page):
        """
        Test form usability on mobile viewport.
        """
        page.goto(BASE_URL)


        page.set_viewport_size({"width": 375, "height": 667})


        expect(page.get_by_placeholder("e.g. Honda", exact=True)).to_be_visible()
        expect(page.get_by_placeholder("e.g. Civic", exact=True)).to_be_visible()
        expect(page.get_by_placeholder("Optional")).to_be_visible()
        expect(page.locator('button:has-text("Search Now")')).to_be_visible()


        self._fill_search_form(page, "Toyota", "Corolla")
        self._submit_form(page)
        expect(page.locator('button:has-text("Searching")')).to_be_visible(timeout=3000)

    def test_clear_search_results(self, page: Page):
        """
        Test "Clear search & show all" resets the view.
        """
        page.goto(BASE_URL)

        self._fill_search_form(page, "Toyota", "Corolla", "2022")
        self._submit_form(page)


        expect(page.get_by_text("FIPE Reference Price")).to_be_visible(timeout=15000)


        clear_button = page.get_by_text("Clear search")
        expect(clear_button).to_be_visible()
        clear_button.click()


        expect(page.get_by_text("FIPE Reference Price")).not_to_be_visible(timeout=3000)


@pytest.mark.e2e
class TestOpportunitiesSearchE2E:
    """Happy path: Mitsubishi Outlander 2016 GT V6 — full cascade → results list."""

    def _select_combobox_option(self, page: Page, button_name: str, filter_text: str):
        """Open a ModelPicker combobox, filter, then JS-click the first matching option."""
        page.get_by_role("button", name=button_name).click()
        page.get_by_role("combobox").last.fill(filter_text)
        page.wait_for_selector("[role=option][data-index='0']", timeout=5000)
        page.evaluate("document.querySelector('[role=option][data-index=\"0\"]').click()")

    def _select_combobox_option_by_text(self, page: Page, button_name: str, contains: str):
        """Open a ModelPicker combobox and JS-click the option whose text contains `contains`."""
        page.get_by_role("button", name=button_name).click()
        page.wait_for_selector("[role=option]", timeout=5000)
        page.evaluate(
            """(text) => {
                const opts = [...document.querySelectorAll('[role=option]')];
                const match = opts.find(o => o.textContent.includes(text));
                if (match) match.click();
            }""",
            contains,
        )

    def test_search_returns_results(self, page: Page):
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(BASE_URL)


        _purge_vehicle("mitsubishi", "outlander", 2016)


        summary_before = requests.get("http://localhost:8000/api/dashboard/summary", timeout=5).json()
        total_before = summary_before["data"]["total_opportunities"]


        page.get_by_role("option", name="M Mitsubishi").click()
        page.wait_for_selector("text=Carregando modelos...", state="hidden", timeout=15000)


        self._select_combobox_option(page, "Modelo", "OUTLANDER")


        page.get_by_role("button", name="2016").click()
        page.wait_for_selector("text=Versão (buscando...)", state="hidden", timeout=15000)


        self._select_combobox_option_by_text(page, "Versão", "GT 3.0 V6")


        page.get_by_role("button", name="Buscar").click()
        expect(page.get_by_text("Buscando...")).to_be_visible(timeout=5000)


        expect(page.get_by_text("Referência FIPE")).to_be_visible(timeout=30000)


        expect(page.get_by_text("Exibindo", exact=False)).to_be_visible()
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible()


        summary_after = requests.get("http://localhost:8000/api/dashboard/summary", timeout=5).json()
        total_after = summary_after["data"]["total_opportunities"]
        assert total_after > total_before, (
            f"Dashboard total_opportunities did not increase "
            f"(before={total_before}, after={total_after})"
        )


        page.wait_for_timeout(5000)
