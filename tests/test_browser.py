"""Browser workflow proof. Requires playwright and installed Google Chrome."""
from pathlib import Path
from datetime import timedelta
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server

with tempfile.TemporaryDirectory() as temporary:
    server.DB = Path(temporary) / 'browser.sqlite'
    server.initialize()
    httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    screenshots = ROOT / 'docs' / 'screenshots'
    screenshots.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 1050}, device_scale_factor=1)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{httpd.server_port}')
            expect(page.get_by_role('heading', name='Your research workspace')).to_be_visible()
            page.screenshot(path=str(screenshots / '01-login.png'), full_page=True)
            page.get_by_role('button', name='Open workspace').click()
            expect(page.get_by_role('heading', name='Research overview')).to_be_visible()
            page.screenshot(path=str(screenshots / '02-overview.png'), full_page=True)
            for name, heading in [('Studies','Study portfolio'),('Visit schedule','Visit schedule'),('Safety & vigilance','Safety & pharmacovigilance'),('Data quality','Data quality'),('Ethics & regulatory','Ethics & regulatory'),('Data exchange','Data exchange'),('Audit trail','Audit & data integrity')]:
                page.get_by_role('navigation').get_by_role('button', name=name).click()
                expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
            expect(page.get_by_text('Chain verified', exact=False)).to_be_visible()
            page.get_by_role('button', name='Verify chain').click()
            expect(page.locator('#toast')).to_contain_text('Hash links intact')
            page.get_by_role('navigation').get_by_role('button', name='Participants', exact=True).click()
            page.get_by_role('button', name='Enrol participant', exact=True).click()
            page.locator('#enrol-form select[name=study_id]').select_option('AIIA-004')
            page.locator('#enrol-form input[type=checkbox]').check()
            page.locator('#enrol-form button[type=submit]').click()
            expect(page.locator('#enrol-form .form-error')).to_contain_text('prospective CTRI')
            page.locator('#enrol-form select[name=study_id]').select_option('AIIA-001')
            page.locator('#enrol-form button[type=submit]').click()
            expect(page.locator('#modal')).not_to_be_visible()
            expect(page.locator('#toast')).to_contain_text('Participant enrolled')
            page.get_by_role('navigation').get_by_role('button', name='Safety & vigilance').click()
            page.get_by_role('button', name='Report adverse event').click()
            page.locator('#event-form input[name=term]').fill('Synthetic browser safety event')
            page.locator('#event-form select[name=seriousness]').select_option('Hospitalisation')
            page.locator('#event-form textarea').fill('Synthetic workflow evidence only.')
            page.locator('#event-form button[type=submit]').click()
            expect(page.locator('#modal')).not_to_be_visible()
            expect(page.locator('td.event-term').filter(has_text='Synthetic browser safety event')).to_be_visible()
            page.screenshot(path=str(screenshots / '03-safety.png'), full_page=True)
            page.get_by_role('navigation').get_by_role('button', name='Data exchange').click()
            with page.expect_download() as downloaded:
                page.get_by_role('button', name='Download JSON').click()
            downloaded.value.save_as(str(Path(temporary) / 'fhir.json'))
            page.get_by_role('navigation').get_by_role('button', name='Studies', exact=True).click()
            page.get_by_role('button', name='New study').click()
            page.locator('#study-form input[name=title]').fill('Synthetic browser activation study')
            page.locator('#study-form input[name=condition]').fill('Workflow validation')
            page.locator('#study-form select[name=type]').select_option('Compound formulation')
            page.locator('#study-form input[name=formulation]').fill('Synthetic formulation for software checks')
            page.locator('#study-form button[type=submit]').click()
            expect(page.get_by_role('button', name='Activate recruitment', exact=True)).to_be_disabled()
            study_id = page.locator('#modal .modal-head p').inner_text().split(' · ')[0]
            page.get_by_role('button', name='Edit study setup').click()
            today = server.utcnow().date()
            setup = {'protocol': 'P-3', 'consent_version': 'ICF-2', 'pi': 'Synthetic investigator', 'batch': 'DEMO-BATCH-BROWSER', 'ctri': 'DEMO-CTRI-BROWSER', 'registered_at': today.isoformat(), 'iec_reference': 'DEMO-IEC-BROWSER', 'iec_approved_at': today.isoformat(), 'iec_expiry': (today + timedelta(days=90)).isoformat()}
            for name, value in setup.items():
                page.locator(f'#study-setup-form input[name={name}]').fill(value)
            page.locator('#study-setup-form textarea[name=reason]').fill('Reviewed synthetic evidence for activation proof.')
            page.locator('#study-setup-form button[type=submit]').click()
            expect(page.get_by_role('heading', name='6 of 6 checks passed')).to_be_visible()
            page.screenshot(path=str(screenshots / '05-study-readiness.png'), full_page=True)
            page.get_by_role('button', name='Activate recruitment', exact=True).click()
            page.locator('#activation-form input[name=reviewed]').check()
            page.locator('#activation-form textarea[name=reason]').fill('Synthetic readiness review completed.')
            page.locator('#activation-form button[type=submit]').click()
            expect(page.locator('#modal')).to_contain_text('Recruiting')
            expect(page.locator('#toast')).to_contain_text('Recruitment activated')
            page.get_by_role('button', name='Close dialog').click()
            page.reload()
            expect(page.get_by_role('heading', name='Research overview')).to_be_visible()
            page.get_by_role('navigation').get_by_role('button', name='Participants', exact=True).click()
            page.get_by_role('button', name='Enrol participant', exact=True).click()
            page.locator('#enrol-form select[name=study_id]').select_option(study_id)
            expect(page.locator('#enrol-form input[name=consent_version]')).to_have_value('ICF-2')
            page.locator('#enrol-form input[name=consent]').check()
            page.locator('#enrol-form button[type=submit]').click()
            expect(page.locator('#toast')).to_contain_text('Participant enrolled')
            page.get_by_role('navigation').get_by_role('button', name='Audit trail').click()
            expect(page.get_by_text('STUDY ACTIVATED', exact=True)).to_be_visible()
            expect(page.get_by_text('Chain verified', exact=False)).to_be_visible()
            page.get_by_role('button', name='Switch demonstration role').click()
            page.locator('select[name=role]').select_option('regulator')
            page.get_by_role('button', name='Open workspace').click()
            expect(page.get_by_role('heading', name='Research overview')).to_be_visible()
            page.get_by_role('navigation').get_by_role('button', name='Participants', exact=True).click()
            expect(page.get_by_role('button', name='Enrol participant')).to_have_count(0)
            page.get_by_role('navigation').get_by_role('button', name='Studies', exact=True).click()
            page.get_by_role('button', name='Synthetic browser activation study', exact=True).click()
            expect(page.get_by_role('button', name='Edit study setup')).to_have_count(0)
            expect(page.get_by_role('button', name='Activate recruitment')).to_have_count(0)
            page.get_by_role('button', name='Close dialog').click()
            page.get_by_role('navigation').get_by_role('button', name='Overview', exact=True).click()
            page.set_viewport_size({'width':390,'height':844})
            page.screenshot(path=str(screenshots / '04-mobile.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile page overflows viewport'
            assert not errors, errors
            browser.close()
            print('PASS: desktop navigation, enrolment gates, SAE, export, setup, readiness, activation, separate consent version, reload, audit, read-only role and mobile layout; no browser errors.')
    finally:
        httpd.shutdown()
        httpd.server_close()
