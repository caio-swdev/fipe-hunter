"""
E2E Test: Favorites Feature

Tests the complete favorites flow including:
- Heart toggle (fill / unfill) with network request validation
- Persistence across navigation (session cookie kept by Playwright)
- Persistence after hard reload (validates MD5 listing-ID fix in search_controller.py)
- Favorites page card display
- Unheart from favorites page removes the card

Architecture notes:
- Session: HttpOnly cookie auto-created on first request (1-year TTL).
  Playwright carries it automatically between requests on the same `page`.
- Heart state: Zustand `favoriteIds` Set, hydrated by Layout via
  GET /api/favorites on every page load.
- Toggle: click heart → optimistic update → POST or DELETE /api/favorites/{id}
- Listing ID after fix: md5(url) — same search re-fires same IDs via URL params on reload.

Implementation notes:
- Use glob pattern "**/api/favorites/**" instead of a lambda predicate for
  `expect_response` — accessing r.request inside a lambda can raise for non-XHR
  responses (e.g. service worker events), causing the context manager to time out.
- Always wait for the API response BEFORE navigating away; 300ms timeouts are
  not sufficient on SQLite write contention.
"""
import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:3001/opportunities"
FAVORITES_URL = "http://localhost:3001/favorites"


_FAV_GLOB = "**/api/favorites/**"


@pytest.mark.e2e
class TestFavoritesE2E:
    """E2E tests for the favorites/heart feature."""


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

    def _do_search(self, page: Page):
        """
        Navigate to /opportunities and perform the Mitsubishi Outlander 2016 GT V6 search.
        Waits until the first "Ver Anúncio" card is visible (results fully loaded).
        """
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(BASE_URL)


        page.get_by_role("option", name="M Mitsubishi").click()
        page.wait_for_selector("text=Carregando modelos...", state="hidden", timeout=15000)


        self._select_combobox_option(page, "Modelo", "OUTLANDER")


        page.get_by_role("button", name="2016").click()
        page.wait_for_selector("text=Versão (buscando...)", state="hidden", timeout=15000)


        self._select_combobox_option_by_text(page, "Versão", "GT 3.0 V6")


        page.get_by_role("button", name="Buscar").click()
        expect(page.get_by_text("Buscando...")).to_be_visible(timeout=5000)


        expect(page.get_by_text("Referência FIPE")).to_be_visible(timeout=30000)


        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=10000)

    def _get_heart_svg_fill(self, page: Page) -> str:
        """
        Return the `fill` attribute of the SVG inside the first heart button.
        lucide-react renders fill as a direct attribute on the <svg> element.
        """
        heart_btn = page.locator(
            'button[title="Adicionar aos favoritos"], button[title="Remover dos favoritos"]'
        ).first
        return heart_btn.locator("svg").get_attribute("fill") or ""

    def _has_any_filled_heart(self, page: Page) -> bool:
        """
        Return True if at least one listing in the current results is favorited.

        Uses the button title rather than the first card's SVG fill — after a
        fresh search the favorited listing may appear at any position in the grid
        (sorted by score), so checking only the first card is unreliable.
        """
        return page.locator('button[title="Remover dos favoritos"]').count() > 0

    def _heart_and_wait(self, page: Page) -> None:
        """
        Click the first unfavorited heart button and wait for the POST response.

        Uses a URL glob pattern instead of a lambda predicate — accessing
        r.request.method inside a lambda can raise for certain browser-internal
        response types, causing expect_response to silently skip the match and
        ultimately time out.
        """
        with page.expect_response(_FAV_GLOB, timeout=10000) as fav_resp:
            page.locator('button[title="Adicionar aos favoritos"]').first.click()

        _ = fav_resp.value

    def _wait_for_favorites_page_loaded(self, page: Page) -> None:
        """
        Wait until the /favorites page has finished loading data.
        Blocks until the page shows either opportunity cards or the empty-state
        message — never returns while the loading spinner is visible.
        """
        page.wait_for_function(
            "() => document.body.innerText.includes('Ver Anúncio') "
            "|| document.body.innerText.includes('Nenhum favorito ainda')",
            timeout=15000,
        )


    def test_heart_fills_on_click(self, page: Page):
        """
        Scenario 1 — Heart fills on click.

        Given results are loaded
        When I click the heart on the first card
        Then the SVG fill becomes "#ef4444"
        And network POST /api/favorites/{id} returns 2xx
        """
        self._do_search(page)


        initial_fill = self._get_heart_svg_fill(page)
        assert initial_fill == "transparent", (
            f"Expected initial fill to be 'transparent', got '{initial_fill}'"
        )


        with page.expect_response(_FAV_GLOB, timeout=10000) as resp_info:
            page.locator('button[title="Adicionar aos favoritos"]').first.click()

        resp = resp_info.value
        assert resp.status < 300, (
            f"POST /api/favorites returned HTTP {resp.status} — expected 2xx"
        )
        assert resp.request.method == "POST", (
            f"Expected POST, got {resp.request.method}"
        )


        page.wait_for_timeout(300)

        filled_fill = self._get_heart_svg_fill(page)
        assert filled_fill == "#ef4444", (
            f"Expected SVG fill '#ef4444' after click, got '{filled_fill}'"
        )

    def test_unheart_empties_heart(self, page: Page):
        """
        Scenario 2 — Unheart empties the heart.

        Given a listing is already hearted (filled)
        When I click the filled heart
        Then the fill becomes "transparent"
        And network DELETE /api/favorites/{id} returns 2xx
        """
        self._do_search(page)


        self._heart_and_wait(page)
        page.wait_for_timeout(300)

        assert self._get_heart_svg_fill(page) == "#ef4444", (
            "Pre-condition failed: heart should be filled before un-hearting"
        )


        with page.expect_response(_FAV_GLOB, timeout=10000) as resp_info:
            page.locator('button[title="Remover dos favoritos"]').first.click()

        resp = resp_info.value
        assert resp.status < 300, (
            f"DELETE /api/favorites returned HTTP {resp.status} — expected 2xx"
        )
        assert resp.request.method == "DELETE", (
            f"Expected DELETE, got {resp.request.method}"
        )

        page.wait_for_timeout(300)

        empty_fill = self._get_heart_svg_fill(page)
        assert empty_fill == "transparent", (
            f"Expected SVG fill 'transparent' after un-hearting, got '{empty_fill}'"
        )

    def test_heart_persists_after_navigate_away_and_back(self, page: Page):
        """
        Scenario 3 — Heart persists after navigating away and back.

        Given I hearted a listing on /opportunities
        When I navigate to /favorites and then to /opportunities and back to /favorites
        Then the listing still appears in /favorites (session cookie preserved, DB intact)

        Note: we verify persistence via /favorites rather than re-running a live OLX
        search.  OLX results are non-deterministic — re-searching may return different
        listings with different md5 IDs, making the /opportunities check unreliable.
        Checking /favorites reads directly from the DB, which is deterministic.
        """
        self._do_search(page)


        self._heart_and_wait(page)


        page.goto(FAVORITES_URL)
        self._wait_for_favorites_page_loaded(page)
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=5000)


        page.goto(BASE_URL)
        page.wait_for_load_state("load")


        page.goto(FAVORITES_URL)
        self._wait_for_favorites_page_loaded(page)
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=5000)

    def test_heart_persists_after_hard_reload(self, page: Page):
        """
        Scenario 4 — Heart persists after hard reload (MD5 fix validation).

        Given I hearted a listing on /opportunities and navigated to /favorites
        When I call page.reload() on the /favorites page
        Then the item is still visible after reload

        This scenario directly validates the MD5 listing-ID fix in
        search_controller.py.  The listing must be saved to the `opportunities`
        table with a STABLE id=md5(url) for the favorite FK to resolve correctly.
        Before the fix, listings without a FIPE price used id=uuid4() and were
        NOT saved to the DB, so GET /api/favorites returned nothing after reload.

        We reload /favorites (not /opportunities) to avoid a second live OLX
        search — OLX results are non-deterministic and would make the assertion
        unreliable.  Reloading /favorites clears the Zustand in-memory state and
        forces a fresh GET /api/favorites, which is the exact hydration path we
        need to validate.
        """
        self._do_search(page)


        self._heart_and_wait(page)


        page.goto(FAVORITES_URL)
        self._wait_for_favorites_page_loaded(page)
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=5000)


        page.reload()
        page.wait_for_load_state("load", timeout=10000)


        self._wait_for_favorites_page_loaded(page)
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=5000)

    def test_favorites_page_shows_hearted_items(self, page: Page):
        """
        Scenario 5 — Favorites page displays hearted items.

        Given I hearted 1 listing on /opportunities
        When I navigate to /favorites
        Then at least 1 listing card is visible on the page
        """
        self._do_search(page)


        self._heart_and_wait(page)


        page.goto(FAVORITES_URL)


        self._wait_for_favorites_page_loaded(page)


        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=5000)

    def test_unheart_from_favorites_removes_card(self, page: Page):
        """
        Scenario 6 — Un-hearting from the favorites page removes the card.

        Given I am on /favorites with 1 saved item
        When I click the filled heart on that item
        Then the card disappears (card count drops to 0)
        And the empty-state message is shown
        """
        self._do_search(page)


        self._heart_and_wait(page)


        page.goto(FAVORITES_URL)
        self._wait_for_favorites_page_loaded(page)
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=5000)


        with page.expect_response(_FAV_GLOB, timeout=10000) as del_resp:
            page.locator('button[title="Remover dos favoritos"]').first.click()
        _ = del_resp.value


        expect(page.get_by_text("Ver Anúncio").first).not_to_be_visible(timeout=10000)


        expect(page.get_by_text("Nenhum favorito ainda")).to_be_visible(timeout=5000)

    def test_heart_active_after_reload_on_opportunities_page(self, page: Page):
        """
        Scenario 7 — Heart icon stays active on /opportunities after a hard reload.

        Given I searched and favorited a listing on /opportunities
        When I hard reload the /opportunities page (URL params are preserved)
        Then the Opportunities page auto-re-runs the same search from URL params
        And the heart icon is still shown as active (filled red) for the same listing

        This is the user-reported regression scenario.  The page stores search
        params in the URL and auto-triggers the search on mount.  After a hard
        reload the Zustand in-memory state is wiped, so the heart can only be
        filled if:
          1. GET /api/favorites re-hydrates the store (Layout useEffect)
          2. The re-search produces the same listing URL → same md5(url) ID
        Both conditions must hold for this test to pass.
        """
        self._do_search(page)


        self._heart_and_wait(page)


        page.reload()
        page.wait_for_load_state("load", timeout=10000)


        expect(page.get_by_text("Referência FIPE")).to_be_visible(timeout=30000)
        expect(page.get_by_text("Ver Anúncio").first).to_be_visible(timeout=10000)


        expect(
            page.locator('button[title="Remover dos favoritos"]').first
        ).to_be_visible(timeout=8000)
