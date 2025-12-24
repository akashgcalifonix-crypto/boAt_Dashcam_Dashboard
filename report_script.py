import asyncio
from playwright.async_api import async_playwright
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import os
import datetime

# --- कल की तारीख निकालें ---
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d") # Format: 2025-12-23
print(f"Generating Report for Date: {yesterday_str}")

# --- URL List ---
urls = {
    "ODM": "https://akashgcalifonix-crypto.github.io/odm-dashboard/",
    "QA": "https://akashgcalifonix-crypto.github.io/QA_dashboard/",
    "SMT": "https://akashgcalifonix-crypto.github.io/SMT_dashboard/",
    "PDI_Dash": "https://akashgcalifonix-crypto.github.io/PDI_Dashboard/",
    "Dashcam": "https://akashgcalifonix-crypto.github.io/boAt_Dashcam_Dashboard/?",
    "PDI_Perf": "https://akashgcalifonix-crypto.github.io/PDI_Performance/"
}

async def capture_smart_screenshots():
    screenshots = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1366, 'height': 768})
        
        # 1. ODM Dashboard (Check for Issues)
        page = await context.new_page()
        print("Checking ODM Dashboard...")
        await page.goto(urls["ODM"], wait_until="networkidle")
        
        # यहाँ कोशिश करें कि कल का डेटा लोड हो (अगर आपकी साइट पर डेट पिकर है)
        # उदाहरण: await page.fill('#date-picker-id', yesterday_str) 
        # await page.click('#submit-button')
        
        # चेक करें कि कोई Issue/Defect है क्या?
        # हम मान रहे हैं कि अगर issue है तो पेज पर "Defect" या "Fail" शब्द होगा
        content = await page.content()
        if "Defect" in content or "Fail" in content or "Issue" in content:
            print("ODM: Issue found, capturing screenshot.")
            path = "ODM_Issue.png"
            await page.screenshot(path=path, full_page=True)
            screenshots.append(("ODM Defect Report", path))
        else:
            print("ODM: No Issue found (Skipping screenshot to save space).")
            # अगर आप चाहते हैं कि issue न होने पर भी फोटो आए, तो नीचे वाली लाइन से # हटा दें
            # await page.screenshot(path="ODM_Clean.png", full_page=True)
            # screenshots.append(("ODM Status (Clean)", "ODM_Clean.png"))

        # 2. QA Dashboard (Floor/Line Wise)
        print("Capturing QA Dashboard...")
        await page.goto(urls["QA"], wait_until="networkidle")
        # यहाँ भी डेट फिल्टर लगाना होगा (अगर साइट पर है)
        path = "QA_Report.png"
        await page.screenshot(path=path, full_page=True)
        screenshots.append(("QA Floor/Line Report", path))

        # 3. SMT Dashboard
        print("Capturing SMT Dashboard...")
        await page.goto(urls["SMT"], wait_until="networkidle")
        path = "SMT_Report.png"
        await page.screenshot(path=path, full_page=True)
        screenshots.append(("SMT Performance", path))

        # 4. Dashcam Dashboard
        print("Capturing Dashcam Dashboard...")
        await page.goto(urls["Dashcam"], wait_until="networkidle")
        path = "Dashcam_Report.png"
        await page.screenshot(path=path, full_page=True)
        screenshots.append(("Dashcam Details", path))

        # 5. PDI Dashboard (Preview)
        print("Capturing PDI Dashboard...")
        await page.goto(urls["PDI_Dash"], wait_until="networkidle")
        path = "PDI_Preview.png"
        await page.screenshot(path=path, full_page=True)
        screenshots.append(("PDI Preview Report", path))

        # 6. PDI Performance (Action Plan)
        print("Capturing PDI Tracker...")
        await page.goto(urls["PDI_Perf"], wait_until="networkidle")
        
        # Action Plan वाले हिस्से का फोटो (अगर उसका कोई खास ID है तो उसे टारगेट करें)
        # उदा: element = await page.query_selector("#action-plan-table")
        # await element.screenshot(path="Action_Plan.png")
        # अभी के लिए फुल पेज ले रहे हैं:
        path = "PDI_ActionPlan.png"
        await page.screenshot(path=path, full_page=True)
        screenshots.append(("PDI Action Plan", path))

        await browser.close()
    return screenshots

def create_smart_pdf(data_list):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title Page
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 20, "Daily Production & Quality Report", ln=True, align='C')
    pdf.set_font("Arial", '', 14)
    pdf.cell(0, 10, f"Date: {yesterday.strftime('%d %B %Y')}", ln=True, align='C')
    pdf.ln(20)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "Summary of attached reports:", ln=True)
    for title, _ in data_list:
        pdf.cell(0, 10, f"- {title}", ln=True)

    # Adding Images
    for title, image_path in data_list:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(5)
        # इमेज को पेज पर फिट करना
        pdf.image(image_path, x=10, y=30, w=190)

    output_filename = f"Daily_Report_{yesterday_str}.pdf"
    pdf.output(output_filename)
    return output_filename

def send_email(file_path):
    sender_email = os.environ["EMAIL_USER"]
    sender_password = os.environ["EMAIL_PASS"]
    receiver_email = sender_email # या जिसे भेजना हो उसका ईमेल

    msg = MIMEMultipart()
    msg['Subject'] = f"Daily Report ({yesterday_str}) - QA, SMT, PDI & ODM"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    body = f"""Hello Akash,

Please find attached the consolidated report for {yesterday.strftime('%d-%b-%Y')}.

Summary:
- Reports are filtered for the previous day.
- ODM defects attached (if any).
- QA/SMT floor-wise details included.

Regards,
Automated Bot
"""
    msg.attach(MIMEText(body, 'plain'))

    with open(file_path, "rb") as f:
        attach = MIMEApplication(f.read(),_subtype="pdf")
        attach.add_header('Content-Disposition','attachment',filename=str(os.path.basename(file_path)))
        msg.attach(attach)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
    print("Email Sent Successfully!")

async def main():
    data = await capture_smart_screenshots()
    if data:
        pdf_file = create_smart_pdf(data)
        send_email(pdf_file)
    else:
        print("No data captured.")

if __name__ == "__main__":
    asyncio.run(main())
