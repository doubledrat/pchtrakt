from pchtrakt.config import *
from lib import requests
import json
import time


from exceptions import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, disable_ssl_verify=False, timeout=30):
        self.V2_API_KEY='a18b7486b102e402e5a627fa3b56b5d54697ec49c05ab9375c85891a48766030'
        self.TRAKT_API_SECRET='b51096526453c72b7dffe868733abda66276d83544bbd5ba9e6093dffc0cab30'
        try:
            config=ConfigParser.RawConfigParser()
            config.read(r'pchtrakt.ini')
            self.TRAKT_ACCESS_TOKEN = config.get('Trakt','api_token')
            self.TRAKT_REFRESH_TOKEN = config.get('Trakt','refresh_token')
            if self.TRAKT_ACCESS_TOKEN == 'None':
                self.TRAKT_ACCESS_TOKEN = None
            if self.TRAKT_REFRESH_TOKEN == 'None':
                self.TRAKT_REFRESH_TOKEN = None
            #else:
            #    self.TRAKT_ACCESS_TOKEN = pchtrakt.config.TRAKT_ACCESS_TOKEN
            #    self.TRAKT_REFRESH_TOKEN = pchtrakt.config.TRAKT_REFRESH_TOKEN
        except:
            self.TRAKT_ACCESS_TOKEN = None
            self.TRAKT_REFRESH_TOKEN = None
        self.verify = not disable_ssl_verify
        self.timeout = timeout if timeout else None
        self.api_url = 'https://api-v2launch.trakt.tv/'
        self.headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': self.V2_API_KEY
        }

    def traktToken(self, TraktPIN=None, refresh=False, count=0):
    
        if count > 3:
            self.TRAKT_ACCESS_TOKEN = ''
            return False
        elif count > 0:
            time.sleep(2)
        
        
        
        data = {
            'client_id': self.V2_API_KEY,
            'client_secret': self.TRAKT_API_SECRET,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
        }
        
        if refresh:
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = self.TRAKT_REFRESH_TOKEN
        else:
            data['grant_type'] = 'authorization_code'
            if not None == TraktPIN:
                data['code'] = TraktPIN
        
        headers = {
            'Content-Type': 'application/json'
        } 
 
        resp = self.traktRequest('oauth/token', data=data,  headers=headers, url=self.api_url , method='POST', count=count)

        if 'access_token' in resp:
            self.TRAKT_ACCESS_TOKEN = resp['access_token']
            # update config
            config=ConfigParser.RawConfigParser()
            config.read(r'pchtrakt.ini')
            config.set('Trakt', 'api_token', self.TRAKT_ACCESS_TOKEN)
            if 'refresh_token' in resp:
                self.TRAKT_REFRESH_TOKEN = resp['refresh_token']
                config.set('Trakt', 'refresh_token', self.TRAKT_REFRESH_TOKEN)
            with open(r'pchtrakt.ini', 'wb') as configfile:
                config.write(configfile)
            return True
        return False
        
    def validateAccount(self):
            
        resp = self.traktRequest('users/settings')
        
        if 'account' in resp:
            myMsg = ' [traktAPI] Welcome %s. ' %(resp['user']['name'])
            if resp['user']['vip']:
                myMsg += ' Your VIP account has been confirmed.'
            else:
                myMsg += ' Your non-vip account has been confirmed.'
            try:
                pchtrakt.logger.info(myMsg)
            except UnicodeEncodeError:
                myMsg = myMsg.encode("utf-8", "replace")
                pchtrakt.logger.info(myMsg)
            return True
        return False
        
    def traktRequest(self, path, data=None, headers=None, url=None, method='GET',count=0):
        if None == url:
            url = self.api_url + path
        else:
            url = url + path
        
        count = count + 1
        
        if None == headers:
            headers = self.headers
        
        if not None == self.TRAKT_ACCESS_TOKEN:
            headers['Authorization'] = 'Bearer ' + self.TRAKT_ACCESS_TOKEN
        
        try:
            resp = requests.request(method, url, headers=headers, timeout=self.timeout,
                data=json.dumps(data) if data else [], verify=self.verify)

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                raise traktException(e)
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                #logger.log(u'Retrying trakt api request: %s' % path, logger.WARNING)
                return self.traktRequest(path, data, headers, method)
            elif code == 401:
                #logger.log(u'Unauthorized. Please check your Trakt settings', logger.WARNING)
                if self.TRAKT_ACCESS_TOKEN == None and self.TRAKT_REFRESH_TOKEN == None:
                    if resp.content != '':
                        #resp=resp.json()
                        if resp.json()[u'error'] == u'invalid_grant':
                            raise traktAuthException(e)
                    elif self.traktToken(TraktPIN=TraktPIN,refresh=False,count=count):
                        return self.traktRequest(path)
                elif self.traktToken(refresh=True,count=count):
                    return self.traktRequest(path, data, url, method)
                raise traktAuthException(e)
            elif code in (500,501,503,504,520,521,522):
                #http://docs.trakt.apiary.io/#introduction/status-codes
                logger.log(u'Trakt may have some issues and it\'s unavailable. Try again later please', logger.WARNING)
                raise traktServerBusy(e)
            else:
                raise traktException(e)

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise traktException(resp['message'])
            if 'error' in resp:
                raise traktException(resp['error'])
            else:
                raise traktException('Unknown Error')

        return resp