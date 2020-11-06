from sec_edgar_downloader import Downloader
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from os import listdir
from os.path import isfile, join


def get_form4(ticker, file_no=10):
    
    # Make sure length makes sense, and file_no an int
    assert len(ticker) < 6
    assert type(file_no) == int

    # Txt files from SEC will populate under this dir
    dl = Downloader("local/test_filing")
    
    # Set ticker to run
    TICK = ticker

    # Downloads FILE_NO most recent form 4's
    dl.get('4', TICK, file_no)
    
    # Enter in directory path to avoid re-downloading files that exist
    mypath = "<YOUR DIR PATH>/local/test_filing/sec_edgar_filings/{}/4/".format(TICK)
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
 
    lines = []
    for f in onlyfiles:
        data_path = "local/test_filing/sec_edgar_filings/{}/4/".format(TICK)
        xblr_string = open(data_path + f).read()
        soup = BeautifulSoup(xblr_string, 'lxml')

        # grab reporting owner
        owner = soup.find_all("rptownername")[0].text

        # Handles the case of someone having multiple classifications
        director = len(soup.find_all("isdirector")) >= 1 and (soup.find_all("isdirector")[0].text.strip() == "1")
        officer = len(soup.find_all("isofficer")) >= 1 and (soup.find_all("isofficer")[0].text.strip() == "1")
        part_owner = len(soup.find_all("istenpercentowner")) >= 1 and (soup.find_all("istenpercentowner")[0].text.strip() == "1")
        who = ""
        if director:
            who += "Director "
        if officer:
            who += "Officer "
        if part_owner:
            who += "TenPercentOwner "
        if len(who) == 0:
            who = "Other"

        tag_list = soup.find_all("nonderivativetransaction")
        # Should be able to find each <nonDerivativeTransaction> and run a for loop
        ### TODO: Add DerivativeTransactions
        
        for tag in tag_list:
            line = {"OWNER": owner, "RELATION": who, "footnote": ""}
            
            # Preliminarily, we'll grab any footnotes
            fnote = tag.find_all('footnoteid')
            if len(fnote) > 0:
                # footnoteid.id corresponds to footnote at bottom of filing
                get_id = fnote[0].attrs["id"]
                line["footnote"] = soup.find('footnote', id=get_id).text

            # Type of security they're trading
            typee = tag.find_all("securitytitle")
            line["SECURITY"] = typee[0].text.strip()

            # How many shares
            share = tag.find_all("transactionshares")
            line["SHARES"] = share[0].text.strip()
            
            # Grab date
            line["DATE"] = tag.find_all("transactiondate")[0].text.strip()
            
            # This line is A if added shares, D if selling ('Disposing')
            added = tag.find_all("transactionacquireddisposedcode")[0].text.strip()
            if added == "D":
                # Negative
                line["SHARES"] = '-' + line["SHARES"]
            
            # Price should be per transaction
            price = tag.find_all("transactionpricepershare")[0].text.strip()
            line["TRANSACTION-PRICE"] = price

            # Direct or indirect ownership, reported as either 'I' or 'D'
            ownership_dict = {"D": "Direct", "I": "Indirect"}
            dir_ownership = tag.find_all('directorindirectownership')[0].text.strip()
            line["DIRECT-or-INDIRECT"] = ownership_dict[dir_ownership]
            
            # How many shares post transaction
            try:
                post_trans = tag.find_all('sharesownedfollowingtransaction')[0].text.strip()
                line["POST-TRANSACTION-SHARES"] = post_trans
                line["POST-TRANSACTION-VALUE"] = "N/A"
            except IndexError:
                post_trans = tag.find_all('posttransactionamounts')[0].text.strip()
                line["POST-TRANSACTION-SHARES"] = "N/A"
                line["POST-TRANSACTION-VALUE"] = post_trans


            lines.append(line)
    return lines

if __name__=="__main__":
    # Example!
    y = [print(x) for x in get_form4("TSLA", file_no=15)]
        
