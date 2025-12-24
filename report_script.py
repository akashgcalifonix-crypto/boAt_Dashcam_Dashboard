import asyncio
from playwright.async_api import async_playwright
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import os
import datetime

# --- कल की तारीख सेट करें ---
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d") # Format: 2025-12-23 (YYYY-MM-DD)
display_date = yesterday.strftime("%d-%b-%Y")

print(f"Targeting Report Date: {yesterday_str}")

urls = {
    "ODM": "https://akashgcalifonix-crypto.github.io/odm-dashboard/",
    "QA": "https://akashgcalifonix-crypto.github.io/QA_dashboard/",
    "SMT": "https://akashgcalifonix-crypto.github.io/SMT_dashboard/",
    "PDI_Dash": "https://akashgcalifonix-crypto.github.io/PDI_Dashboard/",
    "Dashcam": "https://akashgcalifonix-crypto.github.io/boAt_Dashcam_Dashboard/?",
    "PDI_Perf": "https://akashgcalifonix-crypto.github.io/PDI_Performance/"
}

async def capture_and_filter(page, url, name):
    print(f"Opening {name}...")
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(3000) # लोड होने का इंतज़ार

    # --- MAGIC: Date Change Logic ---
    # यह कोड पेज पर 'date' वाले इनपुट को ढूँढकर कल की तारीख भरने की कोशिश करेगा
    try:
        # क्या पेज पर कोई Date Input है?
        date_input = page.locator("input[type='date']").first
        if await date_input.count() > 0:
            print(f"Date input found on {name}, changing date to {yesterday_str}...")
            await date_input.fill(yesterday_str)
            # एंटर दबाएं या कहीं क्लिक करें ताकि डेटा रिफ्रेश हो
            await date_input.press("Enter")
            await page.wait_for_timeout(5000) # डेटा बदलने का इंतज़ार
        else:
            print(f"No date input found on {name}, taking current view.")
    except Exception as e:
        print(f"Could not change date on {name}: {e}")

    # --- Specific Logic for Requirements ---
    
    # 1. ODM: Check for Defects
    if name == "ODM":
        # पेज को नीचे तक स्क्रॉल करें ताकि सब लोड हो जाए
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        content = await page.content()
        # अगर Defect शब्द मिला तो ही रिपोर्ट में जोड़ें
        if "Defect" in content or "Fail" in content or "Issue" in content:
            print("ODM Issue found!")
            path = f"{name}_Issue.png"
            await page.screenshot(path=path, full_page=True)
            return (f"{name} Report (Issues Found)", path)
        else:
             # अगर कोई Issue नहीं है, तो खाली छोड़ दें या क्लीन रिपोर्ट दें
             # अभी हम क्लीन रिपोर्ट ले रहे हैं
             path = f"{name}_Clean.png"
             await page.screenshot(path=path, full_page=True)
             return (f"{name} Report (No Critical Issues)", path)

    # 2. QA/SMT/Dashcam: Full Details
    elif name in ["QA", "SMT", "Dashcam"]:
        # पूरा पेज कैप्चर करें (ताकि Floor/Line details आ जाएं)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        path = f"{name}_Full.png"
        await page.screenshot(path=path, full_page=True)
        return (f"{name} Daily Report", path)

    # 3. PDI: Preview Report & Action Plan
    elif name == "PDI_Perf":
        # Action Plan अक्सर नीचे होता है, स्क्रॉल करें
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        path = f"{name}_ActionPlan.png"
        await page.screenshot(path=path, full_page=True)
        return ("PDI Action Plan", path)
    
    else:
        # Default capture
        path = f"{name}.png"
        await page.screenshot(path=path, full_page=True)
        return (f"{name} Report", path)

async def main_task():
    screenshots = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}) # बड़ी स्क्रीन
        page = await context.new_page()

        for key, url in urls.items():
            result = await capture_and_filter(page, url, key)
            if result:
                screenshots.append(result)
        
        await browser.close()
    return screenshots

def create_pdf(images):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Cover Page
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 20, f"Daily Dashboard Report", ln=True, align='C')
    pdf.set_font("Arial", '', 14)
    pdf.cell(0, 10, f"Date: {display_date}", ln=True, align='C')
    pdf.ln(10)
    
    for title, img_path in images:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True)
        pdf.image(img_path, x=10, y=25, w=190)

    filename = f"Report_{yesterday_str}.pdf"
    pdf.output(filename)
    return filename

def send_email(file_path):
    sender = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    receiver = sender 

    msg = MIMEMultipart()
    msg['Subject'] = f"Combined Report: {display_date}"
    msg['From'] = sender
    msg['To'] = receiver

    body = f"Please find attached the reports for {display_date}.\n\nNote: This report is auto-generated."
    msg.attach(MIMEText(body, 'plain'))

    with open(file_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
        msg.attach(attach)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)
    print("Email Sent!")

if __name__ == "__main__":
    images = asyncio.run(main_task())
    if images:
        pdf = create_pdf(images)
        send_email(pdf)
