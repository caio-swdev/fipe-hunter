"""
E2E Test: FIPE Lookup Vertical Slice

Tests the complete flow from frontend form submission to backend API to result display.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def base_url():
    """Base URL for the application."""
    return "http://localhost:8000"


@pytest.fixture(scope="module")
def browser_context_args(browser_context_args):
    """Configure browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }


class TestFIPELookupE2E:
    """E2E tests for FIPE lookup feature."""

    def test_successful_fipe_lookup(self, page: Page, base_url: str):
        """
        Test successful FIPE lookup flow.

        Steps:
        1. Navigate to the homepage
        2. Fill in brand, model, year
        3. Submit the form
        4. Verify FIPE data is displayed
        """

        page.goto(base_url)


        expect(page).to_have_title("FIPE Hunter - Consulta FIPE")


        brand_input = page.locator('input[name="brand"]')
        model_input = page.locator('input[name="model"]')
        year_input = page.locator('input[name="year"]')
        submit_button = page.locator('button[type="submit"]')

        expect(brand_input).to_be_visible()
        expect(model_input).to_be_visible()
        expect(year_input).to_be_visible()
        expect(submit_button).to_be_visible()


        brand_input.fill("Honda")
        model_input.fill("Civic")
        year_input.fill("2022")


        submit_button.click()


        result_div = page.locator("#result")
        expect(result_div).to_have_class("result success", timeout=5000)


        expect(result_div).to_contain_text("Consulta Realizada")
        expect(result_div).to_contain_text("Marca:")
        expect(result_div).to_contain_text("Honda")
        expect(result_div).to_contain_text("Modelo:")
        expect(result_div).to_contain_text("Civic")
        expect(result_div).to_contain_text("Ano:")
        expect(result_div).to_contain_text("2022")
        expect(result_div).to_contain_text("Código FIPE:")
        expect(result_div).to_contain_text("Preço de Referência:")
        expect(result_div).to_contain_text("R$")

    def test_vehicle_not_found(self, page: Page, base_url: str):
        """
        Test error handling when vehicle is not found in FIPE database.

        Steps:
        1. Navigate to homepage
        2. Fill in with non-existent vehicle data
        3. Submit the form
        4. Verify error message is displayed
        """

        page.goto(base_url)


        page.locator('input[name="brand"]').fill("NonExistentBrand")
        page.locator('input[name="model"]').fill("NonExistentModel")
        page.locator('input[name="year"]').fill("2000")


        page.locator('button[type="submit"]').click()


        result_div = page.locator("#result")
        expect(result_div).to_have_class("result error", timeout=5000)


        expect(result_div).to_contain_text("Erro")

    def test_form_validation(self, page: Page, base_url: str):
        """
        Test form validation for required fields.

        Steps:
        1. Navigate to homepage
        2. Try to submit empty form
        3. Verify HTML5 validation prevents submission
        """

        page.goto(base_url)


        submit_button = page.locator('button[type="submit"]')
        submit_button.click()


        result_div = page.locator("#result")
        expect(result_div).not_to_have_class("result success")
        expect(result_div).not_to_have_class("result error")

    def test_input_trimming(self, page: Page, base_url: str):
        """
        Test that whitespace is trimmed from inputs.

        Steps:
        1. Navigate to homepage
        2. Fill in with values containing whitespace
        3. Submit the form
        4. Verify data is properly trimmed
        """

        page.goto(base_url)


        page.locator('input[name="brand"]').fill("  Honda  ")
        page.locator('input[name="model"]').fill("  Civic  ")
        page.locator('input[name="year"]').fill("2022")


        page.locator('button[type="submit"]').click()


        result_div = page.locator("#result")
        expect(result_div).to_have_class("result success", timeout=5000)


        expect(result_div).to_contain_text("Honda")
        expect(result_div).not_to_contain_text("  Honda  ")

    def test_loading_state(self, page: Page, base_url: str):
        """
        Test that loading state is displayed during API call.

        Steps:
        1. Navigate to homepage
        2. Fill in form
        3. Submit and verify loading indicator appears
        4. Verify button is disabled during submission
        """

        page.goto(base_url)


        page.locator('input[name="brand"]').fill("Honda")
        page.locator('input[name="model"]').fill("Civic")
        page.locator('input[name="year"]').fill("2022")


        submit_button = page.locator('button[type="submit"]')


        submit_button.click()


        expect(submit_button).to_be_disabled()


        result_div = page.locator("#result")
        expect(result_div).to_have_class("result success", timeout=5000)


        expect(submit_button).to_be_enabled()
