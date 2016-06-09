"""
Created on Tue Jun 07 14:42:50 2016

@author: yshen
"""

import requests
import urllib
import json
import re

class AmexOffers:
    
    def __init__(self,username,password):
        self.username=username
        self.acctList=[]
        self.offerList=[]
        self.proxy=None
        self.header={"Content-Type":"application/x-www-form-urlencoded"}
        self.session=requests.Session()
        loginData={"DestPage":"https://online.americanexpress.com/myca/acctmgmt/us/myaccountsummary.do?request_type=authreg_acctAccountSummary&Face=en_US&omnlogin=us_homepage_myca",
                "Face":"en_US",
                "USERID":"",
                "PWD":"",
                "CHECKBOXSTATUS":"",
                "devicePrint":"version%3D1%26pm%5Ffpua%3Dmozilla%2F5%2E0%20%28windows%20nt%206%2E1%3B%20wow64%29%20applewebkit%2F537%2E36%20%28khtml%2C%20like%20gecko%29%20chrome%2F51%2E0%2E2704%2E79%20safari%2F537%2E36%7C5%2E0%20%28Windows%20NT%206%2E1%3B%20WOW64%29%20AppleWebKit%2F537%2E36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F51%2E0%2E2704%2E79%20Safari%2F537%2E36%7CWin32%26pm%5Ffpsc%3D24%7C1920%7C1080%7C1040%26pm%5Ffpsw%3D%26pm%5Ffptz%3D%2D4%26pm%5Ffpln%3Dlang%3Den%2DUS%7Csyslang%3D%7Cuserlang%3D%26pm%5Ffpjv%3D0%26pm%5Ffpco%3D1",
                "brandname":"",
                "TARGET":"",
                "request_type":"IntlLogLogonHandler",
                "Logon":"Continue...",
                "act:soa":"",
                "cardsmanage":"cards",
                "UserID":username,
                "Password":password}
        url="https://online.americanexpress.com/myca/logon/us/action/LogLogonHandler?request_type=LogLogonHandler&Face=en_US"
        r = self.session.post(url,data=loginData,proxies=self.proxy,headers=self.header)  
        parsed=re.findall("(?<=decodeJSONString\(')(.*)(?='\);)",urllib.unquote_plus(r.text))
        if len(parsed)==2:
            self.acctSummary = json.loads(parsed[0].encode('ascii','ignore'))
            self.acctDetail  = json.loads(parsed[1].encode('ascii','ignore'))
            self.zipCode     = self.acctDetail['AccountSummaryBeanList'][0]['cardBean']['zipPostalCode']#gen_data.create_city_state_zip()[0]
            for account in self.acctDetail['AccountSummaryBeanList']:          
                self.acctList.append({'cmName':account['cardBean']['cmName'],
                                 'zipPostalCode':account['cardBean']['zipPostalCode'],
                                 'accountNumber':account['cardBean']['accountNumber'],
                                 'cardProductName':account['cardBean']['cardProductName'],
                                 'encryptedAccountNumber':account['cardBean']['encryptedAccountNumber']})
        else:
            print "Login Failed..."
            
    def findOffers(self):
        for account in self.acctList:       
            requestOffer={"accountNumberStr":account['encryptedAccountNumber'],
                        "channelDef":"LARGE",
                        "currentCardIndex":"3",
                        "eligibleForDPM":"false",
                        "invokeEosSvc":"true",
                        "invokeGoldenGooseSvc":"false",
                        "invokeJetBlueSvc":"false",
                        "invokePaymentStatusSvc":"true",
                        "invokePostedTxnSvc":"false",
                        "invokePznSvc":"true",
                        "loyaltyTier":"PB",
                        "maxNoOfOffers":"9",
                        "onPageLoadFlag":"true",
                        "pmcCode":"158",
                        "pznTipsMsgEligible":"true",
                        "sortedIndex":"3",
                        "zipPostalCode":account['zipPostalCode']}
            
            url="https://online.americanexpress.com/myca/accountsummary/us/onLoadData?request_type=authreg_acctAccountSummary&Face=en_US"
            r = self.session.post(url,data=requestOffer,proxies=self.proxy,headers=self.header)
            
            parsed=json.loads(r.text.encode('ascii','ignore'))
            
            try:
                offers=parsed['eosOffersResponse']['eosOfferBeanList']
                print account['accountNumber'],"Found",parsed['eosOffersResponse']['eosOfferCount'],"offers.."
            except KeyError:
                print account['accountNumber'],"No More Offer..."
                continue
            
            self.offerList+=zip([account['encryptedAccountNumber']]*len(offers),[x['offerId'] for x in offers],[account['zipPostalCode']]*len(offers))
    
    def addOffers(self):
        if len(self.offerList)==0:
            self.findOffers()
            
        for offer in self.offerList:
            addOffer={"accountNumber":offer[0],
                      "offerId":offer[1],
                      "zipPostalCode":offer[2]
                }
            url="https://online.americanexpress.com/myca/accountsummary/us/eosUpdateOffer.do?request_type=authreg_acctAccountSummary&Face=en_US"
            r = self.session.post(url,data=addOffer,proxies=self.proxy,headers=self.header)
            print json.loads(r.text.encode('ascii','ignore'))['updateOfferContentPageBean'][0]['couponlessMessage']
            print json.loads(r.text.encode('ascii','ignore'))['updateOfferContentPageBean'][0]['offerDetailDescription'],'\n'
            
        self.offerList=[]               
        
    def exportOffers(self):
        f=open(self.username+' - AmexOffers.csv','w')
        f.write("accountNumber,cardName,Name,Description,ExpiryDate,Status\n")
        for acct in self.acctList:
            url="https://online.americanexpress.com/myca/accountsummary/us/eosSelectedOffers.do?request_type=authreg_acctAccountSummary&Face=en_US"
            queryOffer={'accountNumber':acct['encryptedAccountNumber'],
                        'touchEnabledDevice':'false'}
            r = self.session.post(url,data=queryOffer,proxies=self.proxy,headers=self.header)
            savedOffers=json.loads(r.text.encode('ascii','ignore'))['selectedOffersList'][0]['selectedOfferPageBean']
            for offer in savedOffers:
                f.write(acct['accountNumber']+","+acct['cardProductName']+",")
                f.write("\""+offer['offerName']+"\",\""+offer['offerDescription']+"\","+offer['offerExpiryDate']+","+offer['selectedOfferStatusHeader']+"\n")
        
        f.close()

###########################################

username=""
password=""

r=AmexOffers(username,password)
r.addOffers()
r.exportOffers()
    
