import yagmail

from core.settings import APP_EMAIL, APP_EMAIL_PASSWORD


def send_email(
    to: str | None = None,
    subject: str | None = None,
    body: str | None = None,
    html: str | None = None,
    img: str | None = None,
):
    contents = []
    if body:
        body += "<br><br>Atenciosamente,<br>Equipe Forquilha"
        contents.append(body)
    elif html:
        html += "<br><br>Atenciosamente,<br>Equipe Forquilha"
        contents.append(html)
    if img:
        contents.append(img)

    with yagmail.SMTP(APP_EMAIL, APP_EMAIL_PASSWORD) as yag:
        if to:
            yag.send(to=to, subject=subject, contents=contents)
        else:
            yag.send(subject=subject, contents=contents)
