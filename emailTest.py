import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

msg = MIMEMultipart()
msg['Subject'] = "Game" 
msg['From'] = "dev.wtobey@gmail.com"
msg['To'] = "dev.wtobey@gmail.com"

part = MIMEBase('application', "octet-stream")
part.set_payload(open("twistd.log", "rb").read())
Encoders.encode_base64(part)

part.add_header('Content-Disposition', 'attachment; filename="twistd.log"')

msg.attach(part)

try:  
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login("dev.wtobey@gmail.com", "openopenopen")
    server.sendmail("dev.wtobey@gmail.com", "dev.wtobey@gmail.com", msg.as_string())
    server.close()

    print 'Email sent!'
except:  
    print 'Something went wrong...'