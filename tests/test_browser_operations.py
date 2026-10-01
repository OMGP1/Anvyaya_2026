"""Exercise operations through installed Chrome, using an isolated synthetic database."""
from pathlib import Path
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
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page(viewport={'width':1440, 'height':1050})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://127.0.0.1:'+str(httpd.server_port))
            page.get_by_role('button', name='Open workspace').click()
            expect(page.get_by_role('heading', name='Research overview')).to_be_visible()

            def navigate(name):
                page.get_by_role('navigation').get_by_role('button', name=name, exact=True).click()

            def submit(form):
                page.locator(form+' button[type=submit]').click()
                expect(page.locator('#modal')).not_to_be_visible()

            def fill(form, values):
                for name, value in values.items():
                    page.locator(form+' [name='+name+']').fill(value)

            navigate('Operations & alerts')
            expect(page.get_by_role('heading', name='Alert inbox', exact=True)).to_be_visible()
            page.get_by_role('button', name='Add site', exact=True).click()
            fill('#operations-site-form', {'code':'BROWSER','name':'Browser test site','city':'Delhi',
                 'investigator':'Synthetic PI','target':'10','reason':'Synthetic site evidence'})
            submit('#operations-site-form')
            row=page.locator('tr').filter(has_text='Browser test site')
            row.get_by_role('button', name='Activate', exact=True).click()
            fill('#operations-site-activate-form', {'reason':'Reviewed the synthetic site record'})
            submit('#operations-site-activate-form')
            expect(row).to_contain_text('Active')
            page.get_by_role('button', name='Plan monitoring', exact=True).click()
            fill('#operations-monitoring-form', {'scope':'Browser monitoring review','reason':'Scheduled source review'})
            submit('#operations-monitoring-form')
            page.locator('tr').filter(has_text='Browser monitoring review').get_by_role('button', name='Complete', exact=True).click()
            fill('#operations-monitoring-complete-form', {'findings':'Source checked during browser run','reason':'Evidence reviewed'})
            submit('#operations-monitoring-complete-form')
            expect(page.locator('section').filter(has=page.get_by_role('heading',name='Monitoring visits',exact=True)).locator('tr').filter(has_text='Browser monitoring review')).to_contain_text('Completed')
            page.get_by_role('button', name='Record deviation', exact=True).click()
            fill('#operations-deviation-form', {'summary':'Browser visit-window deviation','reason':'Source reviewed'})
            submit('#operations-deviation-form')
            page.locator('tr').filter(has_text='Browser visit-window deviation').get_by_role('button',name='Close',exact=True).click()
            fill('#operations-deviation-close-form', {'corrective_action':'Documented corrective action','reason':'Closure reviewed'})
            submit('#operations-deviation-close-form')
            expect(page.locator('tr').filter(has_text='Browser visit-window deviation')).to_contain_text('Closed')
            page.get_by_role('button', name='Open data query', exact=True).click()
            fill('#operations-query-form', {'field':'Browser query field','message':'Check synthetic source','reason':'Monitoring review'})
            submit('#operations-query-form')
            navigate('Data quality')
            page.locator('tr').filter(has_text='Browser query field').get_by_role('button', name='Resolve',exact=True).click()
            fill('#query-form', {'resolution':'Synthetic source reconciled'})
            submit('#query-form')
            navigate('Operations & alerts')
            page.get_by_role('button',name='Edit thresholds',exact=True).click()
            fill('#settings-form', {'monitoring_days':'21','deviation_days':'5'})
            submit('#settings-form')
            expect(page.get_by_role('heading',name='Configured rules')).to_be_visible()
            page.locator('#study-filter').select_option('AIIA-001')
            page.get_by_role('button',name='Pre-inspection report',exact=True).click()
            expect(page.get_by_role('heading', name='Pre-inspection readiness report')).to_be_visible()
            with page.expect_download() as download:
                page.get_by_role('button',name='Download HTML report',exact=True).click()
            report_path=Path(temporary)/'report.html'
            download.value.save_as(report_path)
            assert 'AIIA-001' in report_path.read_text() and 'AIIA-002' not in report_path.read_text()
            assert 'csrf' not in report_path.read_text() and 'session' not in report_path.read_text()
            page.get_by_role('button',name='Close dialog').click()
            page.locator('#study-filter').select_option('')
            page.screenshot(path=str(ROOT/'docs/screenshots/11-operations-alerts.png'), full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.add_style_tag(content='* {transition:none!important; animation:none!important}')
            page.screenshot(path=str(ROOT/'docs/screenshots/12-operations-mobile.png'),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors, errors
            browser.close()
            print('PASS: site activation, monitoring, deviations, queries, thresholds, scoped HTML report, desktop/mobile operations; no JS errors.')
    finally:
        httpd.shutdown()
        httpd.server_close()
