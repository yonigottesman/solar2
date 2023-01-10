from datetime import datetime, timedelta

import aiohttp
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    # 'Accept-Encoding': 'gzip, deflate, br',
    "Content-Type": "multipart/form-data; boundary=---------------------------123289955733948873062906819236",
    "Origin": "https://ssd.jpl.nasa.gov",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://ssd.jpl.nasa.gov/horizons/app.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

data = "-----------------------------123289955733948873062906819236\r\nContent-Disposition: form-data; name=\"www\"\r\n\r\n1\r\n-----------------------------123289955733948873062906819236\r\nContent-Disposition: form-data; name=\"format\"\r\n\r\njson\r\n-----------------------------123289955733948873062906819236\r\nContent-Disposition: form-data; name=\"input\"\r\n\r\n!$$SOF\r\nMAKE_EPHEM=YES\r\nCOMMAND=499\r\nEPHEM_TYPE=OBSERVER\r\nCENTER='coord@399'\r\nCOORD_TYPE=GEODETIC\r\nSITE_COORD='+34.88300,+32.01700,0'\r\nSTART_TIME='${start_time}'\r\nSTOP_TIME='${stop_time}'\r\nSTEP_SIZE='1 MINUTES'\r\nQUANTITIES='20'\r\nREF_SYSTEM='ICRF'\r\nCAL_FORMAT='CAL'\r\nTIME_DIGITS='MINUTES'\r\nANG_FORMAT='HMS'\r\nAPPARENT='AIRLESS'\r\nRANGE_UNITS='AU'\r\nSUPPRESS_RANGE_RATE='NO'\r\nSKIP_DAYLT='NO'\r\nSOLAR_ELONG='0,180'\r\nEXTRA_PREC='NO'\r\nR_T_S_ONLY='NO'\r\nCSV_FORMAT='NO'\r\nOBJ_DATA='YES'\r\n\r\n-----------------------------123289955733948873062906819236--\r\n"


async def query_nasa(start_time, stop_time):
    resolved_data = data.replace("${start_time}", start_time)
    resolved_data = resolved_data.replace("${stop_time}", stop_time)
    async with aiohttp.ClientSession() as session:
        nasa_url = "https://ssd.jpl.nasa.gov/api/horizons_file.api"
        async with session.post(nasa_url, headers=headers, data=resolved_data) as resp:
            return (await resp.json())["result"]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    utcnow = datetime.utcnow()
    today = datetime.strftime(utcnow, "%Y-%m-%d")
    intwodays = datetime.strftime(utcnow + timedelta(days=2), "%Y-%m-%d")
    response = await query_nasa(today, intwodays)

    current_minute = datetime.strftime(utcnow, "%H:%M")

    rows = response.split("\n")
    start = rows.index("$$SOE") + 1
    for r, rp60 in zip(rows[start:], rows[start + 60 :]):
        hour, delta = r.split()[1], r.split()[-2]
        if hour == current_minute:
            au_now = float(delta)
            au_in_an_hour = float(rp60.split()[-2])
            break

    km_now = 149597870.691 * au_now
    km_in_an_hour = 149597870.691 * au_in_an_hour

    return templates.TemplateResponse(
        "index.html", {"request": request, "body": "Mars", "au_now": km_now, "au_in_an_hour": km_in_an_hour}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=4000)
