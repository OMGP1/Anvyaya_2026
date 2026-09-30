"""Named-user evidence, amendment, import and PV workflows in a real browser."""
from datetime import timedelta
from pathlib import Path
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


with tempfile.TemporaryDirectory() as temporary:
    server.DB = Path(temporary) / 'extended.sqlite'
    server.initialize()
    httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 1050})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{httpd.server_port}')
            page.get_by_role('button', name='Open workspace').click()
            expect(page.get_by_role('heading', name='Research overview')).to_be_visible()

            def navigate(name):
                page.get_by_role('navigation').get_by_role('button', name=name, exact=True).click()

            def submit(form):
                page.locator(form + ' button[type=submit]').click()

            def close():
                page.get_by_role('button', name='Close dialog').click()

            def signin(username, first=False):
                page.get_by_role('button', name='Switch demonstration role').click()
                page.get_by_role('button', name='Named account', exact=True).click()
                page.locator('#login-form input[name=username]').fill(username)
                page.locator('#login-form input[name=password]').fill('Temporary#26046' if first else 'Personal#26046Now')
                submit('#login-form')
                if first:
                    expect(page.get_by_role('heading', name='Set your personal password')).to_be_visible()
                    page.locator('#password-form input[name=current_password]').fill('Temporary#26046')
                    page.locator('#password-form input[name=password]').fill('Personal#26046Now')
                    submit('#password-form')
                expect(page.get_by_role('heading', name='Research overview')).to_be_visible()

            navigate('Access management')
            for username, role in [('author.browser','admin'), ('reviewer.browser','ethics')]:
                page.get_by_role('button', name='Create account', exact=True).click()
                page.locator('#user-form input[name=name]').fill(username)
                page.locator('#user-form input[name=username]').fill(username)
                page.locator('#user-form select[name=role]').select_option(role)
                page.locator('#user-form input[name=password]').fill('Temporary#26046')
                if role != 'admin':
                    page.locator('#user-form input[name=scope][value="AIIA-001"]').check()
                submit('#user-form')
                expect(page.locator('#modal')).not_to_be_visible()
            page.screenshot(path=str(ROOT/'docs/screenshots/06-access-management.png'), full_page=True)
            signin('author.browser', True)
            navigate('Documents & amendments')
            for kind, version in [('Protocol','P-3'),('Consent','ICF-3'),('IEC','IEC-3')]:
                page.get_by_role('button', name='Upload evidence', exact=True).click()
                page.locator('#document-form select[name=study_id]').select_option('AIIA-001')
                page.locator('#document-form select[name=kind]').select_option(kind)
                page.locator('#document-form input[name=version]').fill(version)
                page.locator('#document-form input[name=file]').set_input_files({'name': kind.lower()+'.txt','mimeType':'text/plain','buffer':b'Synthetic evidence for browser workflow verification.'})
                submit('#document-form')
                expect(page.locator('#modal')).not_to_be_visible()
            page.locator('tr').filter(has_text='protocol.txt').get_by_role('button', name='Review', exact=True).click()
            page.locator('#document-review-form textarea').fill('Self review should be rejected.')
            submit('#document-review-form')
            expect(page.locator('#document-review-form .form-error')).to_contain_text('different')
            close()
            signin('reviewer.browser', True)
            navigate('Documents & amendments')
            for filename in ['protocol.txt','consent.txt','iec.txt']:
                row = page.locator('tr').filter(has_text=filename)
                row.get_by_role('button', name='Review', exact=True).click()
                page.locator('#document-review-form textarea').fill('Independently checked the synthetic source document.')
                submit('#document-review-form')
                expect(page.locator('#modal')).not_to_be_visible()
                expect(row).to_contain_text('Approved')
            signin('author.browser')
            navigate('Documents & amendments')
            page.get_by_role('button', name='Submit amendment', exact=True).click()
            page.locator('#amendment-form textarea').fill('Approved synthetic protocol and consent change.')
            submit('#amendment-form')
            expect(page.locator('#modal')).not_to_be_visible()
            signin('reviewer.browser')
            navigate('Documents & amendments')
            page.get_by_role('button', name='Approve', exact=True).click()
            page.locator('#amendment-approve-form textarea').fill('Independent amendment approval; current participants require reconsent.')
            submit('#amendment-approve-form')
            expect(page.locator('#modal')).not_to_be_visible()
            expect(page.get_by_text('38 participants require reconsent')).to_be_visible()
            page.screenshot(path=str(ROOT/'docs/screenshots/07-documents-amendments.png'), full_page=True)
            signin('author.browser')
            navigate('Participants')
            row = page.locator('tr').filter(has_text='SYN-01-003')
            row.get_by_role('button', name='Record reconsent').click()
            expect(page.locator('#reconsent-form input[name=consent_version]')).to_have_value('ICF-3')
            page.locator('#reconsent-form input[name=consent]').check()
            page.locator('#reconsent-form textarea').fill('New synthetic consent reviewed and documented.')
            submit('#reconsent-form')
            expect(page.locator('#modal')).not_to_be_visible()
            expect(row).to_contain_text('Active · vICF-3')
            row.get_by_role('button', name='History', exact=True).click()
            expect(page.locator('#modal')).to_contain_text('2.1')
            close()
            navigate('Integration & evidence')
            page.get_by_role('button', name='Import synthetic CSV').click()
            page.locator('#import-form input[name=synthetic]').check()
            submit('#import-form')
            expect(page.get_by_role('heading', name='Source review', exact=False)).to_be_visible()
            page.locator('#import-commit-form input[name=reviewed]').check()
            page.locator('#import-commit-form textarea').fill('Reviewed synthetic mapped source and current consent.')
            submit('#import-commit-form')
            expect(page.locator('#modal')).to_contain_text('1 participants added')
            close()
            page.get_by_role('button', name='Check current FHIR links').click()
            expect(page.locator('#modal')).to_contain_text('All local references resolve')
            expect(page.locator('#modal .pill')).to_have_count(4)
            close()
            page.screenshot(path=str(ROOT/'docs/screenshots/08-integration-evidence.png'), full_page=True)
            page.get_by_role('button', name='Terminology packages', exact=True).click()
            submit('#safety-dictionary-form')
            expect(page.locator('#modal')).to_contain_text('demo-1')
            close()
            navigate('Safety & vigilance')
            page.locator('[data-action="event-detail"][data-id="AE-0003"]').click()
            page.get_by_role('button', name='Review code suggestions').click()
            submit('#safety-suggestions-form')
            page.locator('tr').filter(has_text='DEMO-NAUSEA').get_by_role('button', name='Review this code').click()
            page.locator('#safety-coding-form textarea').fill('Reviewed fictional terminology candidate for this synthetic event.')
            submit('#safety-coding-form')
            expect(page.locator('#modal')).to_contain_text('Reviewed synthetic coding')
            expect(page.locator('#modal')).to_contain_text('DEMO-NAUSEA')
            page.get_by_role('button', name='Add recipient obligation').click()
            page.locator('#safety-obligation-form input[name=recipient]').fill('Synthetic IEC recipient')
            due = server.utcnow() + timedelta(hours=12)
            page.locator('#safety-obligation-form input[name=due_at]').fill(due.astimezone().isoformat()[:19])
            page.locator('#safety-obligation-form textarea').fill('Synthetic internal SOP target for recipient follow-up.')
            submit('#safety-obligation-form')
            expect(page.locator('#modal')).to_contain_text('Awaiting dispatch')
            page.get_by_role('button', name='Record escalation', exact=True).click()
            page.locator('#safety-followup-form textarea').fill('Recorded a synthetic internal follow-up; no message sent.')
            submit('#safety-followup-form')
            expect(page.locator('#modal')).to_contain_text('1 escalations')
            for operation in ['dispatch','receipt']:
                page.get_by_role('button', name='Record '+operation, exact=True).click()
                page.locator('#safety-followup-form input[name=reference]').fill('SYNTHETIC-'+operation.upper())
                page.locator('#safety-followup-form textarea').fill('Recorded synthetic external '+operation+' evidence.')
                submit('#safety-followup-form')
                expect(page.locator('#modal')).to_contain_text('Awaiting receipt' if operation=='dispatch' else 'Acknowledged')
            page.screenshot(path=str(ROOT/'docs/screenshots/10-coding-followup.png'), full_page=True)
            close()
            navigate('Integration & evidence')
            page.emulate_media(reduced_motion='reduce')
            page.set_viewport_size({'width':390,'height':844})
            page.screenshot(path=str(ROOT/'docs/screenshots/09-integration-mobile.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile horizontal overflow'
            assert not errors, errors
            browser.close()
            print('PASS: named accounts, forced password change, independent evidence review, amendment, reconsent, import, FHIR checks, terminology review, recipient follow-up and responsive layout.')
    finally:
        httpd.shutdown()
        httpd.server_close()
