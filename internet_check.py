import http.client


# Check if internet connection available using the google main site
def check_internet(url_internet="https://www.google.com/", timeout=5):
    connect_internet = http.client.HTTPConnection(url_internet, timeout=timeout)
    try:
        connect_internet.request("head", "/")
        connect_internet.close()
        return True
    except:
        return False
