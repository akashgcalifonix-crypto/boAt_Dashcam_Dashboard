import asyncio
from playwright.async_api import async_playwright
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import os
import datetime

# आपके 6 डैशबोर्ड लिंक
urls = [
    "https://akashgcalifonix-crypto.github.io/odm-dashboard/",
    "https://akashgcalifonix-crypto.github.io/QA_dashboard/",
    "https://akashgcalifonix-crypto.github.io/SMT_dashboard/",
    "https://akashgcalifonix-crypto.github.io/PDI_Dashboard/",
    "https://akashgcalifonix-crypto.github.io/boAt_Dashcam_Dashboard/?",
    "https://akashgcalifonix-crypto.github.io/PDI_Performance/"
]

async def take_screenshots():
    screenshot_files = []
    async with async_playwright() as p:
        print("Launching Browser...")
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        
        for i, url in enumerate(urls):
            print(f"Opening: {url}")
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                # थोड़ा और इंतज़ार ताकि चार्ट लोड हो जाएं
                await page.wait_for_timeout(5000) 
                filename = f"dash_{i}.png"
                await page.screenshot(path=filename, full_page=True)
                screenshot_files.append(filename)
            except Exception as e:
                print(f"Error on {url}: {e}")
            await page.close()
            
        await browser.close()
    return screenshot_files

def create_pdf(images):
    print("Creating PDF...")
    pdf = FPDF()
    for image in images:
        pdf.add_page()
        # इमेज को पेज पर सेट करना
        pdf.image(image, x=10, y=10, w=190)
    
    output_filename = f"Report_{datetime.date.today()}.pdf"
    pdf.output(output_filename)
    return output_filename

def send_email(file_path):
    print("Sending Email...")
    sender_email = os.environ["EMAIL_USER"]
    sender_password = os.environ["EMAIL_PASS"]
    # जिस ईमेल पर रिपोर्ट चाहिए (यहाँ Sender को ही भेज रहे हैं)
    receiver_email = sender_email 

    msg = MIMEMultipart()
    msg['Subject'] = f"Daily Report: {datetime.date.today()}"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    body = "Hello Akash,\n\nHere is your daily combined report of all dashboards."
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
    images = await take_screenshots()
    if images:
        pdf_file = create_pdf(images)
        send_email(pdf_file)
    else:
        print("No screenshots taken.")

if __name__ == "__main__":
    asyncio.run(main())
